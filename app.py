# app.py
# FastAPI backend for your AI Maturity Assessment demo
#
# How to use:
# 1) Put your big HTML into a file named: index.html (same folder as this app.py)
# 2) Run locally:
#    pip install fastapi uvicorn python-multipart
#    uvicorn app:app --reload --port 8001
# 3) Deploy to Render:
#    Start command: uvicorn app:app --host 0.0.0.0 --port $PORT
#
# Notes:
# - This demo uses in-memory storage. If the server restarts, submissions reset.
# - /api/transcribe-note returns whisper_available=false by default (no Whisper installed).
# - The analysis is "demo-realistic": category averages, composite stage, per-question confidence/evidence,
#   follow-up queue, and reanalysis after interview answers.

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="AHI Maturity Assessment Backend", version="1.0.0")

# Allow same-origin and simple dev testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for demo; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")

# -----------------------------
# In-memory "DB"
# -----------------------------
SUBMISSIONS: Dict[str, Dict[str, Any]] = {}  # submission_id -> analysis blob + payload
SESSIONS: Dict[str, Dict[str, Any]] = {}     # session_id -> session state


# -----------------------------
# Helpers
# -----------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def safe_text(s: Optional[str]) -> str:
    return (s or "").strip()

def short_excerpt(s: str, n: int = 180) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n] + ("…" if len(s) > n else "")

def stage_from_composite(x: float) -> Tuple[str, str]:
    # Match your front-end stage naming roughly
    if x <= 2.19:
        return ("Nascent", "Foundational stage. AI interest is isolated. You lack the consistent data readiness and ownership needed to scale.")
    if x <= 3.19:
        return ("Exploring", "Initial practices are emerging. Scale requires tighter alignment across business and tech units.")
    if x <= 4.19:
        return ("Established", "Standardized stage. You have clear capability. Focus on scaling your operating model and tracking ROI.")
    return ("Leading", "Advanced stage. AI is a core strategic lever. Predictive decisioning and automated governance are primary goals.")

def infer_stage(score: Optional[int], typed: Optional[str], has_tagged_note: bool) -> int:
    """
    Convert a 1-5 self score into a stage 1-5 with small adjustments for evidence.
    This is a demo heuristic.
    """
    if score is None:
        return 0
    base = int(clamp(score, 1, 5))
    evidence_bonus = 1 if (safe_text(typed) or has_tagged_note) else 0
    # If they gave evidence and scored high, slightly reinforce; if no evidence and high score, slightly soften
    if base >= 4 and evidence_bonus == 0:
        return max(1, base - 1)
    if base <= 2 and evidence_bonus == 1:
        return min(5, base + 1)
    return base

def confidence_label(score: Optional[int], typed: Optional[str], has_tagged_note: bool) -> str:
    """
    Low if high score but no evidence, or score missing.
    Med if some evidence, High if evidence + consistency.
    """
    if score is None:
        return "Low"
    t = bool(safe_text(typed))
    if score >= 4 and not (t or has_tagged_note):
        return "Low"
    if (t or has_tagged_note) and score >= 3:
        return "High"
    if (t or has_tagged_note):
        return "Med"
    return "Med" if score <= 2 else "Low"

def evidence_strength_label(typed: Optional[str], has_tagged_note: bool) -> str:
    if safe_text(typed) and has_tagged_note:
        return "Strong"
    if safe_text(typed) or has_tagged_note:
        return "Moderate"
    return "None"

def detect_contradiction(score: Optional[int], typed: Optional[str]) -> bool:
    """
    Demo contradiction detector:
    - High score but typed text includes strong negation words.
    """
    if score is None:
        return False
    text = safe_text(typed).lower()
    if not text:
        return False
    neg = any(w in text for w in ["no ", "not ", "never", "none", "don't", "do not", "lacking", "absence"])
    if score >= 4 and neg:
        return True
    return False

def default_followup_probe(qid: str, label: str, category: str) -> str:
    return (
        f"For **{qid} - {label}** ({category}), can you give 1-2 concrete examples "
        "from the last 90 days (owners, metrics, tools, artifacts, policies, or incidents)? "
        "If it is not in place, what is the specific blocker?"
    )

def build_hybrid_analyst(role: Optional[str], composite: float) -> Optional[Dict[str, Any]]:
    if not role:
        return None
    # Demo benchmark distribution by role
    mean = 3.2
    std = 0.6
    z = (composite - mean) / std if std else 0.0
    z = float(clamp(z, -3.0, 3.0))

    gaps: List[str] = []
    if z > 1.0:
        gaps.append("Respondent scores maturity materially ABOVE benchmark - verify with artifacts (roadmaps, governance, logs).")
    if z < -1.0:
        gaps.append("Respondent scores maturity materially BELOW benchmark - check if role has limited visibility into enterprise initiatives.")
    if not gaps:
        gaps.append("No major perception gap vs benchmark.")

    outliers: List[str] = []
    if abs(z) >= 2.0:
        outliers.append("High outlier signal - re-check several ‘4-5’ ratings without evidence.")

    interp = "Near benchmark."
    if z > 0.75:
        interp = "Above benchmark - likely more optimistic or closer to initiatives."
    if z < -0.75:
        interp = "Below benchmark - likely more risk-focused or less visibility."

    return {
        "role_compared_to": role,
        "respondent_zscore": z,
        "benchmark_note": f"Benchmark is a demo distribution for role={role}.",
        "zscore_interpretation": interp,
        "perception_gaps": gaps,
        "outlier_flags": outliers,
    }


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def serve_index() -> HTMLResponse:
    if not os.path.exists(INDEX_HTML_PATH):
        return HTMLResponse(
            content=(
                "<h2>Missing index.html</h2>"
                "<p>Create <code>index.html</code> in the same folder as <code>app.py</code> and paste your HTML there.</p>"
            ),
            status_code=200,
        )
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.post("/api/transcribe-note")
async def transcribe_note(audio: UploadFile = File(...)) -> JSONResponse:
    # Demo default: no Whisper installed.
    # If you later add Whisper, swap this to real transcription.
    _ = await audio.read()
    return JSONResponse(
        {
            "whisper_available": False,
            "transcript": None,
            "detail": "Whisper not installed in this build."
        }
    )


@app.post("/api/analyze-assessment")
async def analyze_assessment(payload: Dict[str, Any]) -> JSONResponse:
    """
    Accepts the payload your front-end sends in collectPhase1Payload().
    Returns a rich analysis object used by renderPhase1AgentResults().
    """
    submission_id = str(uuid.uuid4())

    questions: List[Dict[str, Any]] = payload.get("questions") or []
    justifications: List[Dict[str, Any]] = payload.get("justifications") or []

    # Map justifications to question_id (tag_id), grouped by category
    note_by_qid: Dict[str, bool] = {}
    note_text_by_qid: Dict[str, str] = {}
    for j in justifications:
        tag_id = safe_text(j.get("tag_id"))
        text = safe_text(j.get("text"))
        if tag_id and tag_id != "GENERAL":
            note_by_qid[tag_id] = True
            if text:
                note_text_by_qid[tag_id] = (note_text_by_qid.get(tag_id, "") + " " + text).strip()

    # Category summaries
    cat_sum: Dict[str, float] = {}
    cat_count: Dict[str, int] = {}

    per_question: List[Dict[str, Any]] = []
    followup_queue: List[Dict[str, Any]] = []

    for q in questions:
        qid = safe_text(q.get("question_id"))
        category = safe_text(q.get("category")) or "Unknown"
        label = safe_text(q.get("label")) or qid or "Question"
        score = q.get("score")
        typed = q.get("typed_response")

        score_int: Optional[int]
        try:
            score_int = int(score) if score is not None else None
        except Exception:
            score_int = None

        has_note = bool(note_by_qid.get(qid, False))
        inferred = infer_stage(score_int, typed, has_note)
        conf = confidence_label(score_int, typed, has_note)
        ev = evidence_strength_label(typed, has_note)

        # supporting excerpt: typed first, else tagged note snippet
        excerpt_source = safe_text(typed) or note_text_by_qid.get(qid, "")
        excerpt = short_excerpt(excerpt_source, 220) if excerpt_source else None

        # evidence id only if there is some excerpt
        evidence_id = str(uuid.uuid4()) if excerpt else None

        red_flags: List[str] = []
        if conf == "Low":
            red_flags.append("Low confidence - score lacks supporting evidence.")
        if detect_contradiction(score_int, typed):
            red_flags.append("Contradiction detected - high score but typed response contains strong negation.")
            # prioritize contradictions
        if score_int is None:
            # If unscored, we still include it but don't flag it for followup
            pass

        recommended_followups: List[str] = []
        if (conf == "Low" or any("Contradiction" in rf for rf in red_flags)) and score_int is not None:
            recommended_followups.append(default_followup_probe(qid, label, category))
            recommended_followups.append("What artifact would prove this is in place (policy, KPI dashboard, roadmap, training completion report, access controls)?")

        pq = {
            "question_id": qid,
            "category": category,
            "label": label,
            "self_score": score_int,
            "inferred_stage": inferred,
            "confidence_label": conf,
            "evidence_strength_label": ev,
            "supporting_text_excerpt": excerpt,
            "evidence_id": evidence_id,
            "red_flags": red_flags,
            "recommended_followups": recommended_followups,
            # extra fields your UI references (optional)
            "confidence": {"High": 0.85, "Med": 0.6, "Low": 0.35}.get(conf, 0.35),
        }
        per_question.append(pq)

        # Category averages for scored questions
        if score_int is not None:
            cat_sum[category] = cat_sum.get(category, 0.0) + float(score_int)
            cat_count[category] = cat_count.get(category, 0) + 1

        # Build follow-up queue items (optional; UI can build client-side too)
        if recommended_followups and score_int is not None:
            priority = "medium"
            if any("Contradiction" in rf for rf in red_flags):
                priority = "high"
            if any("Low confidence" in rf for rf in red_flags) and score_int >= 4:
                priority = "critical"

            followup_queue.append(
                {
                    "question_id": qid,
                    "category": category,
                    "label": label,
                    "priority": priority,
                    "reason": red_flags,
                    "probe": recommended_followups[0],
                    "prior_score": score_int,
                    "confidence": pq["confidence"],
                    "supporting_text_excerpt": excerpt,
                }
            )

    # Dimensions array (category cards)
    dimensions: List[Dict[str, Any]] = []
    for cat, total in cat_sum.items():
        cnt = cat_count.get(cat, 0)
        avg = (total / cnt) if cnt else None
        if avg is None:
            continue
        # confidence per dimension from its per_question items
        cat_qs = [pq for pq in per_question if pq["category"] == cat and pq["self_score"] is not None]
        low_ct = sum(1 for pq in cat_qs if pq["confidence_label"] == "Low")
        if low_ct >= max(1, len(cat_qs) // 2):
            dim_conf = "Low"
            flags = ["Many items lacked evidence - validate this category."]
        elif low_ct > 0:
            dim_conf = "Med"
            flags = ["Some items need verification."]
        else:
            dim_conf = "High"
            flags = []
        dimensions.append(
            {
                "category": cat,
                "avg_score": float(round(avg, 2)),
                "question_count": cnt,
                "confidence_label": dim_conf,
                "summary_flags": flags,
            }
        )

    # Composite score from category averages
    cat_avgs = [(cat_sum[c] / cat_count[c]) for c in cat_sum if cat_count.get(c, 0) > 0]
    composite = float(round(sum(cat_avgs) / len(cat_avgs), 2)) if cat_avgs else 0.0
    maturity_stage, stage_blurb = stage_from_composite(composite)

    # Top blockers / quick wins (simple heuristics)
    blockers: List[str] = []
    quick_wins: List[str] = []
    next_best_actions: List[str] = []

    # If lots of low confidence, blockers
    low_conf = [pq for pq in per_question if pq["confidence_label"] == "Low" and pq["self_score"] is not None]
    if len(low_conf) >= 3:
        blockers.append("Ratings are frequently unsupported by artifacts - establish evidence capture (policy links, dashboards, owners) to reduce ambiguity.")
        quick_wins.append("Add one proof artifact per ‘4-5’ rating (link or short excerpt) - instantly improves diagnostic confidence.")
    # If governance shadow AI appears
    for pq in per_question:
        if pq["question_id"].lower().startswith("g_shadow") and pq["self_score"] and pq["self_score"] <= 3:
            blockers.append("Shadow AI risk - unmanaged use of external tools and uncontrolled data sharing.")
            next_best_actions.append("Publish an approved AI tools list + data handling policy + light monitoring within 30 days.")
            break

    # Add generic NBAs
    next_best_actions.extend([
        "Create an AI use-case intake process (owner, value, risk, data, timeline) and run 3 pilots with clear ROI metrics.",
        "Stand up a lightweight AI governance cadence: monthly decisions, risk register, and approvals tied to deployment gates.",
    ])

    # Hybrid analyst
    respondent_role = payload.get("respondent_role")
    hybrid_analyst = build_hybrid_analyst(respondent_role, composite)

    overall = {
        "composite_score": composite,
        "maturity_stage": maturity_stage,
        "assessment_quality_note": stage_blurb,
        "needs_human_followup": True if followup_queue else False,
    }

    # Persist
    analysis_blob = {
        "submission_id": submission_id,
        "created_at": now_iso(),
        "overall": overall,
        "dimensions": dimensions,
        "per_question": per_question,
        "top_blockers": blockers,
        "quick_wins": quick_wins,
        "next_best_actions": next_best_actions,
        "hybrid_analyst": hybrid_analyst,
        "followup_queue": followup_queue,
        # Optional metadata for your debugging bar
        "respondent_name": payload.get("respondent_name"),
        "organization_name": payload.get("organization_name"),
    }

    SUBMISSIONS[submission_id] = {
        "payload": payload,
        "analysis": analysis_blob,
    }

    return JSONResponse(analysis_blob)


@app.post("/api/v2/session/start")
async def session_start(body: Dict[str, Any]) -> JSONResponse:
    """
    Starts a follow-up interview session.
    Expects:
      - followup_queue: [question_id, ...]
      - probe_overrides: {question_id: text}
      - respondent_name, organization_name, etc (optional)
    """
    session_id = str(uuid.uuid4())
    qids: List[str] = body.get("followup_queue") or []
    probe_overrides: Dict[str, str] = body.get("probe_overrides") or {}

    # Build queue objects
    queue: List[Dict[str, Any]] = []
    for qid in qids:
        probe = probe_overrides.get(qid) or f"Can you add evidence/details for {qid}?"
        queue.append({"question_id": qid, "probe": probe})

    SESSIONS[session_id] = {
        "created_at": now_iso(),
        "mode": body.get("mode") or "B",
        "queue": queue,
        "idx": 0,
        "answers": {},  # qid -> text
        "respondent_name": body.get("respondent_name"),
        "organization_name": body.get("organization_name"),
        "respondent_role": body.get("respondent_role"),
        "organization_unit": body.get("organization_unit"),
        "selected_sections": body.get("selected_sections") or [],
    }

    greeting = "Follow-up interview started. Answer briefly but specifically - owners, metrics, artifacts, and dates help."
    first_probe = queue[0]["probe"] if queue else "No follow-up items."
    opening_text = f"{greeting}\n\n{first_probe}"

    return JSONResponse({"session_id": session_id, "opening_text": opening_text})


@app.post("/api/v2/session/turn")
async def session_turn(body: Dict[str, Any]) -> JSONResponse:
    """
    Handles one user turn in the interview.
    For simplicity:
    - If user says "skip", store empty and advance.
    - Otherwise store answer against current question_id.
    - Ends when queue is complete, returns compiled_payload.
    """
    session_id = body.get("session_id")
    user_text = safe_text(body.get("user_text"))

    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")

    s = SESSIONS[session_id]
    queue = s["queue"]
    idx = int(s["idx"])

    if idx >= len(queue):
        # Already complete
        compiled = _compiled_payload_from_session(s)
        return JSONResponse({"is_complete": True, "compiled_payload": compiled})

    current_qid = queue[idx]["question_id"]

    # Basic state machine:
    # - If user response is too short, ask clarify and DO NOT advance.
    # - If "skip", advance.
    # - Else store answer and advance.
    if user_text.lower() == "skip":
        s["answers"][current_qid] = ""
        s["idx"] = idx + 1
        idx = s["idx"]
        if idx >= len(queue):
            compiled = _compiled_payload_from_session(s)
            return JSONResponse({"is_complete": True, "compiled_payload": compiled})
        return JSONResponse({"is_complete": False, "state": "ASK", "assistant_text": queue[idx]["probe"]})

    if len(user_text) < 12:
        return JSONResponse(
            {
                "is_complete": False,
                "state": "CLARIFY",
                "assistant_text": "Can you add one concrete detail (owner, metric, artifact, tool, or date)?"
            }
        )

    s["answers"][current_qid] = user_text
    s["idx"] = idx + 1
    idx = s["idx"]

    if idx >= len(queue):
        compiled = _compiled_payload_from_session(s)
        # Optionally we can also return refreshed_analysis if we can find a submission_id
        # (Your frontend can also call /reanalyze; returning refreshed analysis is a nice shortcut.)
        return JSONResponse({"is_complete": True, "compiled_payload": compiled})

    # Ask next question
    return JSONResponse({"is_complete": False, "state": "ASK", "assistant_text": queue[idx]["probe"]})


def _compiled_payload_from_session(s: Dict[str, Any]) -> Dict[str, Any]:
    # Shape matches your frontend expectation: compiledPayload.questions[]
    questions = []
    for qid, txt in (s.get("answers") or {}).items():
        questions.append({"question_id": qid, "typed_response": txt or None})
    return {
        "payload_version": "1.0",
        "respondent_name": s.get("respondent_name"),
        "organization_name": s.get("organization_name"),
        "respondent_role": s.get("respondent_role"),
        "organization_unit": s.get("organization_unit"),
        "selected_sections": s.get("selected_sections") or [],
        "questions": questions,
    }


@app.post("/api/submissions/{submission_id}/reanalyze")
async def reanalyze_submission(submission_id: str, body: Dict[str, Any]) -> JSONResponse:
    """
    Accepts { answers: [{question_id, text_response}, ...] }
    Updates stored payload (typed_response fields) and reruns analysis.
    """
    record = SUBMISSIONS.get(submission_id)
    if not record:
        raise HTTPException(status_code=404, detail="Submission not found in memory (server may have restarted).")

    payload = record["payload"]
    answers = body.get("answers") or []

    patch = {safe_text(a.get("question_id")): safe_text(a.get("text_response")) for a in answers if a.get("question_id")}
    # Update payload.questions typed_response
    for q in payload.get("questions") or []:
        qid = safe_text(q.get("question_id"))
        if qid in patch and patch[qid]:
            q["typed_response"] = patch[qid]

    # Re-run analysis but keep same submission_id for your UI
    refreshed = await analyze_assessment(payload)
    refreshed_obj = refreshed.body
    # refreshed.body is bytes in FastAPI JSONResponse; easier: rebuild directly:
    # We'll recompute and then force submission_id to remain the same.
    refreshed_dict = SUBMISSIONS[list(SUBMISSIONS.keys())[-1]]["analysis"]  # latest created by analyze_assessment
    refreshed_dict["submission_id"] = submission_id
    SUBMISSIONS[submission_id]["analysis"] = refreshed_dict
    # Remove the extra temporary submission that analyze_assessment created
    # (last key is the new one - delete it)
    temp_keys = [k for k in SUBMISSIONS.keys() if k != submission_id]
    # Keep original and delete the latest if it isn't the original
    if temp_keys:
        # The analyze_assessment call created a new submission_id.
        # We delete that newest record to avoid memory growth.
        newest = temp_keys[-1]
        SUBMISSIONS.pop(newest, None)

    return JSONResponse(SUBMISSIONS[submission_id]["analysis"])


@app.post("/api/simulate-followup")
async def simulate_followup(body: Dict[str, Any]) -> JSONResponse:
    """
    Creates simulated answers for the flagged questions and re-runs analysis.
    Expects: { submission_id, style }
    """
    submission_id = safe_text(body.get("submission_id"))
    style = safe_text(body.get("style")) or "strong_specific"

    record = SUBMISSIONS.get(submission_id)
    if not record:
        raise HTTPException(status_code=404, detail="Submission not found in memory (server may have restarted).")

    payload = record["payload"]
    analysis = record["analysis"]
    flagged = analysis.get("followup_queue") or []

    def gen_answer(qid: str, style_: str) -> str:
        if style_ == "vague":
            return "We have some initiatives and people are working on it. It is improving."
        if style_ == "contradictory":
            return "We rate this highly, but honestly there is no formal process and it rarely happens."
        if style_ == "executive":
            return "This is owned by the exec sponsor, reviewed monthly, tracked via KPIs, and tied to funding decisions."
        if style_ == "technical":
            return "We have a documented process, automated checks, logs/monitoring, and deployment gates in CI/CD."
        # strong_specific
        return "Owner: VP/CTO. Artifact: roadmap + KPI dashboard. Cadence: monthly. Evidence: last review 2 weeks ago with decisions logged."

    simulated_qids: List[str] = []
    # Apply simulated answers to payload.questions
    qmap = {safe_text(q.get("question_id")): q for q in (payload.get("questions") or [])}
    for item in flagged:
        qid = safe_text(item.get("question_id"))
        if not qid or qid not in qmap:
            continue
        qmap[qid]["typed_response"] = gen_answer(qid, style)
        simulated_qids.append(qid)

    # Re-run analysis and persist under same submission_id
    refreshed = await reanalyze_submission(submission_id, {"answers": [{"question_id": q, "text_response": qmap[q]["typed_response"]} for q in simulated_qids]})
    refreshed_dict = SUBMISSIONS[submission_id]["analysis"]

    return JSONResponse(
        {
            "submission_id": submission_id,
            "style": style,
            "simulated_count": len(simulated_qids),
            "simulated_qids": simulated_qids,
            "refreshed_analysis": refreshed_dict,
        }
    )


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "time": now_iso(),
        "submissions_in_memory": len(SUBMISSIONS),
        "sessions_in_memory": len(SESSIONS),
    }