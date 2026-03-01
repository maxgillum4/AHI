"""
routes.py — AHI Diagnostic Reasoning Engine
FastAPI route handlers. Thin layer: validate, analyze, benchmark, return.
No business logic lives here — it all lives in analyzer.py and hybrid_analyst.py.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from typing import List, Optional

from pydantic import BaseModel

from analyzer import analyze_assessment
from db.repository import get_submission, mark_followups_resolved, save_submission, update_submission_result
from hybrid_analyst import generate_hybrid_summary
from schema import EXAMPLE_PAYLOAD, AnalysisResponse, AssessmentPayload, QuestionResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/analyze-assessment
# ---------------------------------------------------------------------------
import os
import tempfile

# Whisper is optional — not available on hosted deployments without ffmpeg.
# The app degrades gracefully: audio recording buttons are still shown but
# transcription returns whisper_available=False.
try:
    import whisper as _whisper
    _model = _whisper.load_model("base")
    _whisper_available = True
    print("[AHI] Whisper loaded successfully.")
except Exception as _whisper_err:
    _model = None
    _whisper_available = False
    print(f"[AHI] Whisper unavailable (hosted mode — audio transcription disabled): {_whisper_err}")


@router.post("/transcribe-note")
async def transcribe_note(audio: UploadFile = File(...)) -> JSONResponse:
    if not _whisper_available or _model is None:
        return JSONResponse(
            status_code=200,
            content={"transcript": None, "whisper_available": False,
                     "error": "Audio transcription is not available in this deployment."},
        )

    tmp_path = None
    try:
        suffix = os.path.splitext(audio.filename or "")[1] or ".m4a" or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            contents = await audio.read()
            print(f"[TRANSCRIBE] filename={audio.filename} content_type={audio.content_type}")
            print(f"[TRANSCRIBE] bytes={len(contents)} suffix={suffix} tmp={tmp_path}")
            tmp.write(contents)

        result = _model.transcribe(tmp_path, language="en", task="transcribe")
        transcript = (result.get("text") or "").strip()
        language = result.get("language")
        segments = result.get("segments")
        print(f"[TRANSCRIBE] text_len={len(transcript)} lang={language} segs={0 if not segments else len(segments)}")
        return JSONResponse(content={
            "transcript": transcript,
            "language": language,
            "segments": segments,
            "whisper_available": True,
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"transcript": None, "whisper_available": True, "error": str(e)},
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    

@router.post("/analyze-assessment", response_model=AnalysisResponse)
async def analyze_assessment_endpoint(
    payload: AssessmentPayload,
    request: Request,
) -> AnalysisResponse:
    """
    Primary diagnostic endpoint.

    Pipeline:
      1. Validate payload (Pydantic handles this automatically)
      2. Run ReasoningModule (analyzer.py)
      3. Attach HybridAnalystSummary (hybrid_analyst.py, if benchmark data available)
      4. Return AnalysisResponse

    NDA note: No raw text or audio is persisted. Analysis is performed in RAM.
    Justification text is used only for signal extraction and is not logged.
    """
    submission_id = str(uuid.uuid4())

    try:
        # Step 2: Core analysis
        result = analyze_assessment(payload)

        # Step 3: Statistical benchmarking (optional — fails gracefully)
        try:
            hybrid = generate_hybrid_summary(payload, result)
            result = result.model_copy(update={"hybrid_analyst": hybrid})
        except Exception:
            # Benchmark failure is non-fatal — continue without it
            pass

        # Step 4: Persist submission + results (non-fatal)
        try:
            save_submission(submission_id, payload, result)
        except Exception as db_err:
            print(f"[AHI] DB persistence error (non-fatal): {db_err}")

        # Step 5: Attach submission_id to response so frontend can reference it
        result = result.model_copy(update={"submission_id": submission_id})
        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis engine error: {type(e).__name__}: {str(e)}"
        )


# ---------------------------------------------------------------------------
# GET /api/schema/example-payload
# ---------------------------------------------------------------------------

@router.get("/schema/example-payload")
async def example_payload() -> JSONResponse:
    """
    Returns a fully valid example payload.
    Useful for frontend developers testing the API without a running assessment.
    """
    return JSONResponse(content=EXAMPLE_PAYLOAD)


# ---------------------------------------------------------------------------
# GET /api/debug/submission/{submission_id}  — pipeline diagnostic
# ---------------------------------------------------------------------------

@router.get("/debug/submission/{submission_id}")
async def debug_submission(submission_id: str) -> JSONResponse:
    """
    Diagnostic endpoint — shows raw DB state for a persisted submission.
    Useful for validating the Phase 1 → reanalysis → refreshed-result pipeline.
    Remove before external client delivery.
    """
    data = get_submission(submission_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Submission not found.")

    sub = data["submission"]
    pqs = data["per_question"]

    return JSONResponse(content={
        "pipeline_check": {
            "submission_found":        True,
            "submission_id":           sub.get("submission_id"),
            "respondent_name":         sub.get("respondent_name"),
            "composite_score":         sub.get("composite_score"),
            "maturity_stage":          sub.get("maturity_stage"),
            "needs_human_followup":    bool(sub.get("needs_human_followup")),
            "submitted_at":            sub.get("submitted_at"),
            "question_count":          sub.get("question_count"),
        },
        "per_question_summary": [
            {
                "question_id":            r.get("question_id"),
                "evidence_id":            r.get("evidence_id"),
                "confidence_label":       r.get("confidence_label"),
                "inferred_stage":         r.get("inferred_stage"),
                "followup_resolved":      bool(r.get("followup_resolved")),
                "has_supporting_excerpt": bool(r.get("supporting_text_excerpt")),
            }
            for r in pqs
        ],
        "reanalysis_status": {
            "any_followup_resolved":   any(r.get("followup_resolved") for r in pqs),
            "resolved_count":          sum(1 for r in pqs if r.get("followup_resolved")),
            "evidence_ids_present":    sum(1 for r in pqs if r.get("evidence_id")),
            "total_questions":         len(pqs),
        },
    })


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health() -> dict:
    """Health check — also reports benchmark data availability."""
    from hybrid_analyst import BENCHMARK_CSV, load_benchmark

    df = load_benchmark()
    benchmark_status = (
        f"loaded ({len(df)} respondents)"
        if not df.empty
        else "not available (run generate_benchmark.py)"
    )

    return {
        "status": "ok",
        "version": "1.0",
        "phase": "phase_1_structured_analyzer",
        "benchmark": benchmark_status,
    }


# ---------------------------------------------------------------------------
# GET /api/submissions/{submission_id}
# ---------------------------------------------------------------------------

@router.get("/submissions/{submission_id}")
async def get_submission_endpoint(submission_id: str) -> JSONResponse:
    """
    Retrieve a persisted submission by ID.

    Returns the submission header and all per-question results.
    Useful for trust panel UI and follow-up session bootstrapping.
    NDA: supporting_text_excerpt fields are PII-redacted at analysis time.
    """
    data = get_submission(submission_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return JSONResponse(content=data)


# ---------------------------------------------------------------------------
# POST /api/submissions/{submission_id}/reanalyze  (Chunk 3)
# ---------------------------------------------------------------------------

class _AnswerPatch(BaseModel):
    question_id:   str
    text_response: Optional[str] = None


class _ReanalyzeRequest(BaseModel):
    answers: List[_AnswerPatch]


@router.post("/submissions/{submission_id}/reanalyze", response_model=AnalysisResponse)
async def reanalyze_submission(
    submission_id: str,
    body: _ReanalyzeRequest,
) -> AnalysisResponse:
    """
    Re-run Phase 1 analysis after a follow-up interview.

    Accepts per-question follow-up text, merges with original scores from the
    persisted submission, re-runs the analyzer, updates the DB, and returns
    the refreshed AnalysisResponse.

    NDA: follow-up text is used in-memory for analysis only; the PII-redacted
         excerpt from the re-analysis is what gets persisted.
    """
    sub_data = get_submission(submission_id)
    if sub_data is None:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Build question bank lookup for prompt text
    from phase2.question_bank import QUESTIONS as _QB
    _qbank = {q.question_id: q for q in _QB}

    # Build answer patch map
    answer_map = {
        a.question_id: a.text_response
        for a in body.answers
        if a.text_response
    }

    # Reconstruct AssessmentPayload from DB + patches
    q_responses: List[QuestionResponse] = []
    for row in sub_data["per_question"]:
        qid    = row["question_id"]
        q_obj  = _qbank.get(qid)
        prompt = q_obj.prompt if q_obj else row.get("label", qid)
        q_responses.append(QuestionResponse(
            question_id    = qid,
            category       = row["category"],
            label          = row.get("label", ""),
            prompt         = prompt,
            score          = row.get("self_score"),
            typed_response = answer_map.get(qid),
        ))

    if not q_responses:
        raise HTTPException(status_code=400, detail="No questions found in submission.")

    sub_header = sub_data["submission"]
    payload = AssessmentPayload(
        payload_version   = sub_header.get("payload_version", "1.0"),
        respondent_name   = sub_header["respondent_name"],
        organization_name = sub_header["organization_name"],
        respondent_role   = sub_header.get("respondent_role"),
        organization_unit = sub_header.get("organization_unit"),
        selected_sections = [],
        questions         = q_responses,
        justifications    = [],
    )

    try:
        result = analyze_assessment(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-analysis error: {e}")

    try:
        hybrid = generate_hybrid_summary(payload, result)
        result = result.model_copy(update={"hybrid_analyst": hybrid})
    except Exception:
        pass

    result = result.model_copy(update={"submission_id": submission_id})

    # Persist refreshed result
    try:
        update_submission_result(submission_id, result)
        if answer_map:
            mark_followups_resolved(submission_id, set(answer_map.keys()))
    except Exception as db_err:
        print(f"[AHI] reanalyze DB error (non-fatal): {db_err}")

    return result


# ---------------------------------------------------------------------------
# POST /api/simulate-followup  — Follow-up simulation harness
# ---------------------------------------------------------------------------

# Realistic synthetic answers keyed by (style, category).
# The "default" key is used when no category-specific answer is defined.
_SIM_ANSWERS: dict[str, dict[str, str]] = {
    "strong_specific": {
        "Leadership & Vision": (
            "Our Chief Data Officer (Dr. Sarah Chen) holds full accountability. "
            "We have a quarterly AI steering committee that reports directly to the board, "
            "and we track ROI via a Tableau dashboard — current return is 2.1x across "
            "our three deployed models. Any initiative over $250k requires explicit CDO sign-off."
        ),
        "Ways of Working": (
            "The AI Centre of Excellence — six people, led by Marcus Webb — coordinates "
            "all cross-functional AI decisions. We run biweekly sprints with product and tech, "
            "and disputes are resolved via a documented RACI approved last October."
        ),
        "Culture & Workforce": (
            "Jane Smith, Head of Learning, owns this directly. We track monthly completion "
            "rate in Workday Learning — currently 78%, up from 52% six months ago. "
            "Mandatory AI literacy modules launched in Q3 for all staff above band 4."
        ),
        "Governance Readiness": (
            "Our AI Risk Committee reviews every deployment monthly using a formal risk "
            "register in Jira. We halted one model from going live in March after bias "
            "testing flagged a 12% disparity across demographic segments."
        ),
        "Technology Readiness": (
            "We run on AWS SageMaker with MLflow for experiment tracking. "
            "P95 inference latency is 140ms. Model monitoring via Evidently AI triggers "
            "retraining when input PSI drift exceeds 0.05 on production features."
        ),
        "Data Readiness": (
            "The CRM domain is our most mature — ISO 8000 certified, 99.2% completeness "
            "in Alation. A net-new labeled training dataset takes 3–4 weeks through "
            "our in-house annotation pipeline."
        ),
        "default": (
            "Alex Rivera, VP Operations, owns this directly and reports monthly to the "
            "executive team. We track it via a balanced scorecard — currently at 71% against "
            "our 12-month target. Full review occurs every quarter with documented outcomes."
        ),
    },
    "vague": {
        "default": (
            "We've been working on improving this area for a while. "
            "The team is aware of the importance and we're making good progress. "
            "There are ongoing discussions about the best approach going forward."
        ),
    },
    "contradictory": {
        "default": (
            "Yes, we have a very mature, well-defined process with clear ownership in place. "
            "Actually, we're still figuring out who should lead this — it's split between IT "
            "and the business units right now. But leadership is fully aligned and we expect "
            "to resolve the ownership question in the next planning cycle."
        ),
    },
    "executive": {
        "default": (
            "AI is a top strategic priority that's fully endorsed at the board level. "
            "We've committed significant multi-year investment and have strong executive "
            "sponsorship across the C-suite. The transformation programme is well underway "
            "with clear momentum behind it."
        ),
    },
    "technical": {
        "default": (
            "We use a federated learning architecture with differential privacy guarantees "
            "(epsilon=1.0). Our feature store (Feast) serves 400+ features at p99 latency "
            "under 50ms. Retraining is automated via Kubeflow Pipelines, triggered when "
            "a KS-test p-value drops below 0.05 on the production input distribution."
        ),
    },
}


def _generate_sim_answers(pq_rows: list, style: str) -> dict[str, str]:
    """
    Build a {question_id: answer_text} map for questions that were flagged in Phase 1.
    Only questions with red_flags or recommended_followups receive simulated answers.
    """
    style_bank = _SIM_ANSWERS.get(style, _SIM_ANSWERS["vague"])
    answers: dict[str, str] = {}
    for row in pq_rows:
        has_flags = bool(row.get("red_flags") or row.get("recommended_followups"))
        if not has_flags:
            continue
        category = row.get("category", "")
        answer = style_bank.get(category) or style_bank.get("default", "")
        if answer:
            answers[row["question_id"]] = answer
    return answers


class _SimulateFollowupRequest(BaseModel):
    submission_id: str
    style: str = "strong_specific"   # strong_specific | vague | contradictory | executive | technical


@router.post("/simulate-followup")
async def simulate_followup(body: _SimulateFollowupRequest) -> JSONResponse:
    """
    Run a complete follow-up simulation without user interaction.

    Generates synthetic respondent answers for all flagged questions based on
    the requested style, re-runs Phase 1 analysis with those answers, persists
    the result, and returns the refreshed AnalysisResponse.

    Styles:
      strong_specific  — named owners, KPIs, systems, cadence (raises confidence)
      vague            — no concrete anchors (should trigger low confidence)
      contradictory    — self-contradicting statements
      executive        — high-level alignment language, no operational detail
      technical        — deep technical detail, weak governance/ownership signals

    NDA: simulated answers are used in-memory only for re-analysis.
    """
    valid_styles = {"strong_specific", "vague", "contradictory", "executive", "technical"}
    if body.style not in valid_styles:
        raise HTTPException(
            status_code=422,
            detail=f"style must be one of: {', '.join(sorted(valid_styles))}",
        )

    sub_data = get_submission(body.submission_id)
    if sub_data is None:
        raise HTTPException(status_code=404, detail="Submission not found.")

    sub_header = sub_data["submission"]
    pq_rows    = sub_data["per_question"]

    # Generate simulated answers for flagged questions only
    sim_answers = _generate_sim_answers(pq_rows, body.style)
    if not sim_answers:
        raise HTTPException(
            status_code=400,
            detail="No flagged questions found in this submission to simulate.",
        )

    # Reconstruct AssessmentPayload with simulated answers patched in
    from phase2.question_bank import QUESTIONS as _QB
    _qbank = {q.question_id: q for q in _QB}

    q_responses: List[QuestionResponse] = []
    for row in pq_rows:
        qid   = row["question_id"]
        q_obj = _qbank.get(qid)
        prompt = q_obj.prompt if q_obj else row.get("label", qid)
        q_responses.append(QuestionResponse(
            question_id    = qid,
            category       = row["category"],
            label          = row.get("label", ""),
            prompt         = prompt,
            score          = row.get("self_score"),
            typed_response = sim_answers.get(qid),
        ))

    payload = AssessmentPayload(
        payload_version   = sub_header.get("payload_version", "1.0"),
        respondent_name   = sub_header["respondent_name"],
        organization_name = sub_header["organization_name"],
        respondent_role   = sub_header.get("respondent_role"),
        organization_unit = sub_header.get("organization_unit"),
        selected_sections = [],
        questions         = q_responses,
        justifications    = [],
    )

    try:
        result = analyze_assessment(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation analysis error: {e}")

    try:
        hybrid = generate_hybrid_summary(payload, result)
        result = result.model_copy(update={"hybrid_analyst": hybrid})
    except Exception:
        pass

    result = result.model_copy(update={"submission_id": body.submission_id})

    # Persist refreshed result and mark simulated questions as resolved
    try:
        update_submission_result(body.submission_id, result)
        mark_followups_resolved(body.submission_id, set(sim_answers.keys()))
    except Exception as db_err:
        print(f"[AHI] simulate-followup DB error (non-fatal): {db_err}")

    return JSONResponse(content={
        "style":            body.style,
        "simulated_count":  len(sim_answers),
        "simulated_qids":   list(sim_answers.keys()),
        "refreshed_analysis": result.model_dump(),
    })
