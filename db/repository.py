"""
db/repository.py — AHI persistence operations.

Public surface:
    save_submission(submission_id, payload, result)                    -> None  (Chunk 1)
    get_submission(submission_id)                                      -> dict | None  (Chunk 2)
    update_submission_result(submission_id, result, resolved_question_id) -> None  (Chunk 2)
    mark_followups_resolved(submission_id, question_ids)               -> None  (Chunk 3)

NDA note: only PII-redacted analysis outputs are written.
          Raw justification text is never stored here.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from .database import get_connection

if TYPE_CHECKING:
    from schema import AnalysisResponse, AssessmentPayload


# ---------------------------------------------------------------------------
# Chunk 1 — initial save
# ---------------------------------------------------------------------------

def save_submission(
    submission_id: str,
    payload: "AssessmentPayload",
    result: "AnalysisResponse",
) -> None:
    """
    Persist one assessment submission and its per-question analysis results.

    Idempotent on submission_id (INSERT OR IGNORE) so retries don't duplicate rows.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO submissions (
                submission_id, respondent_name, organization_name,
                respondent_role, organization_unit, payload_version,
                submitted_at, composite_score, maturity_stage,
                needs_human_followup, question_count,
                top_blockers, quick_wins, next_best_actions
            ) VALUES (
                :submission_id, :respondent_name, :organization_name,
                :respondent_role, :organization_unit, :payload_version,
                :submitted_at, :composite_score, :maturity_stage,
                :needs_human_followup, :question_count,
                :top_blockers, :quick_wins, :next_best_actions
            )
            """,
            {
                "submission_id":        submission_id,
                "respondent_name":      result.respondent_name,
                "organization_name":    result.organization_name,
                "respondent_role":      payload.respondent_role.value
                                        if payload.respondent_role else None,
                "organization_unit":    payload.organization_unit,
                "payload_version":      payload.payload_version,
                "submitted_at":         now_iso,
                "composite_score":      result.overall.composite_score,
                "maturity_stage":       result.overall.maturity_stage,
                "needs_human_followup": int(result.overall.needs_human_followup),
                "question_count":       len(result.per_question),
                "top_blockers":         json.dumps(result.top_blockers),
                "quick_wins":           json.dumps(result.quick_wins),
                "next_best_actions":    json.dumps(result.next_best_actions),
            },
        )

        for pqr in result.per_question:
            _insert_pqr(conn, submission_id, pqr, resolved=False, use_ignore=True)


# ---------------------------------------------------------------------------
# Chunk 2 — read
# ---------------------------------------------------------------------------

def get_submission(submission_id: str) -> Optional[dict]:
    """
    Return the full persisted submission as a plain dict, or None if not found.

    Shape:
      {
        "submission": { ...header fields... },
        "per_question": [ { ...row fields... }, ... ]
      }
    """
    with get_connection() as conn:
        sub_row = conn.execute(
            "SELECT * FROM submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()

        if sub_row is None:
            return None

        pqr_rows = conn.execute(
            "SELECT * FROM per_question_results WHERE submission_id = ? ORDER BY id",
            (submission_id,),
        ).fetchall()

    def _deserialize_pqr(row) -> dict:
        d = dict(row)
        d["red_flags"]             = json.loads(d["red_flags"] or "[]")
        d["recommended_followups"] = json.loads(d["recommended_followups"] or "[]")
        d["followup_resolved"]     = bool(d.get("followup_resolved", 0))
        return d

    sub_dict = dict(sub_row)
    sub_dict["top_blockers"]     = json.loads(sub_dict.get("top_blockers") or "[]")
    sub_dict["quick_wins"]       = json.loads(sub_dict.get("quick_wins") or "[]")
    sub_dict["next_best_actions"] = json.loads(sub_dict.get("next_best_actions") or "[]")

    return {
        "submission":  sub_dict,
        "per_question": [_deserialize_pqr(r) for r in pqr_rows],
    }


# ---------------------------------------------------------------------------
# Chunk 2 — update after follow-up reanalysis
# ---------------------------------------------------------------------------

def update_submission_result(
    submission_id: str,
    result: "AnalysisResponse",
    resolved_question_id: Optional[str] = None,
) -> None:
    """
    Replace the submission header + per-question rows with refreshed analysis.

    If resolved_question_id is supplied, that question's row is marked
    followup_resolved=True in the new data.
    """
    with get_connection() as conn:
        # Update header row
        conn.execute(
            """
            UPDATE submissions SET
                composite_score      = :composite_score,
                maturity_stage       = :maturity_stage,
                needs_human_followup = :needs_human_followup,
                question_count       = :question_count,
                top_blockers         = :top_blockers,
                quick_wins           = :quick_wins,
                next_best_actions    = :next_best_actions
            WHERE submission_id = :submission_id
            """,
            {
                "submission_id":        submission_id,
                "composite_score":      result.overall.composite_score,
                "maturity_stage":       result.overall.maturity_stage,
                "needs_human_followup": int(result.overall.needs_human_followup),
                "question_count":       len(result.per_question),
                "top_blockers":         json.dumps(result.top_blockers),
                "quick_wins":           json.dumps(result.quick_wins),
                "next_best_actions":    json.dumps(result.next_best_actions),
            },
        )

        # Replace per-question rows
        for pqr in result.per_question:
            resolved = (
                resolved_question_id is not None
                and pqr.question_id == resolved_question_id
            )
            _insert_pqr(conn, submission_id, pqr, resolved=resolved, use_ignore=False)


# ---------------------------------------------------------------------------
# Chunk 3 — bulk resolved marking (for multi-question reanalyze endpoint)
# ---------------------------------------------------------------------------

def mark_followups_resolved(submission_id: str, question_ids: set) -> None:
    """
    Mark a set of per_question_results rows as followup_resolved=1.
    Called after a multi-question reanalysis to record which questions
    were addressed in the follow-up interview.
    """
    if not question_ids:
        return
    with get_connection() as conn:
        for qid in question_ids:
            conn.execute(
                """
                UPDATE per_question_results
                SET followup_resolved = 1
                WHERE submission_id = ? AND question_id = ?
                """,
                (submission_id, qid),
            )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _insert_pqr(conn, submission_id: str, pqr, resolved: bool, use_ignore: bool) -> None:
    """Insert or replace one per_question_result row."""
    row_id     = f"{submission_id}:{pqr.question_id}"
    conflict   = "OR IGNORE" if use_ignore else "OR REPLACE"

    conn.execute(
        f"""
        INSERT {conflict} INTO per_question_results (
            id, submission_id, question_id, category, label,
            self_score, inferred_stage, confidence, confidence_label,
            evidence_strength, evidence_strength_label, evidence_id,
            has_supporting_audio, mentions_metric, mentions_owner,
            mentions_cadence, mentions_system,
            red_flags, recommended_followups, supporting_text_excerpt,
            followup_resolved
        ) VALUES (
            :id, :submission_id, :question_id, :category, :label,
            :self_score, :inferred_stage, :confidence, :confidence_label,
            :evidence_strength, :evidence_strength_label, :evidence_id,
            :has_supporting_audio, :mentions_metric, :mentions_owner,
            :mentions_cadence, :mentions_system,
            :red_flags, :recommended_followups, :supporting_text_excerpt,
            :followup_resolved
        )
        """,
        {
            "id":                      row_id,
            "submission_id":           submission_id,
            "question_id":             pqr.question_id,
            "category":                pqr.category,
            "label":                   pqr.label,
            "self_score":              pqr.self_score,
            "inferred_stage":          pqr.inferred_stage,
            "confidence":              pqr.confidence,
            "confidence_label":        pqr.confidence_label.value,
            "evidence_strength":       pqr.evidence_strength,
            "evidence_strength_label": pqr.evidence_strength_label.value,
            "evidence_id":             pqr.evidence_id,
            "has_supporting_audio":    int(pqr.has_supporting_audio),
            "mentions_metric":         int(pqr.mentions_metric),
            "mentions_owner":          int(pqr.mentions_owner),
            "mentions_cadence":        int(pqr.mentions_cadence),
            "mentions_system":         int(pqr.mentions_system),
            "red_flags":               json.dumps(pqr.red_flags),
            "recommended_followups":   json.dumps(pqr.recommended_followups),
            "supporting_text_excerpt": pqr.supporting_text_excerpt,
            "followup_resolved":       int(resolved),
        },
    )
