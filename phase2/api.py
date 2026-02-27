"""
phase2/api.py — Phase 2 FastAPI router.

Conversational interview engine endpoints, mounted at /api/v2 in main.py.

Endpoints:
  GET  /api/v2/health
  GET  /api/v2/questions
  POST /api/v2/session/start
  POST /api/v2/session/turn
  GET  /api/v2/session/{session_id}
  DELETE /api/v2/session/{session_id}

NDA:
  - Turn text is stored in RAM only for the session lifetime (max 2h TTL).
  - Transcript content is never written to logs — only lengths and IDs.
  - Audio bytes are never accepted here (v2 accepts text only).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from .generation.template_generator import TemplateGenerator
from .question_bank import QUESTIONS, filter_by_sections, get_question
from .schemas import (
    ConversationState,
    ConversationTurn,
    ExtractedAnswer,
    InterviewMode,
    QuestionBankItem,
    QuestionBankResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionStatusResponse,
    TurnRequest,
    TurnResponse,
    V2Session,
)
from .state_machine import TransitionResult, is_skip, next_state, should_wrap
from .storage import store
from .utils import build_generator

router = APIRouter()

# Single shared generator instance (TemplateGenerator is stateless)
_generator = build_generator()


# ---------------------------------------------------------------------------
# GET /api/v2/health
# ---------------------------------------------------------------------------

@router.get("/health")
async def v2_health() -> dict:
    """Phase 2 health check — reports generation mode and active session count."""
    from .utils import get_generation_mode
    return {
        "status": "ok",
        "version": "2.0",
        "phase": "phase_2_conversational_engine",
        "chunk": "1_foundation",
        "generation_mode": get_generation_mode(),
        "active_sessions": store.count(),
        "question_bank_size": len(QUESTIONS),
    }


# ---------------------------------------------------------------------------
# GET /api/v2/questions
# ---------------------------------------------------------------------------

@router.get("/questions", response_model=QuestionBankResponse)
async def get_questions(
    sections: Optional[str] = Query(
        None,
        description="Comma-separated section keys, e.g. leadership,tech,data",
    ),
) -> QuestionBankResponse:
    """Return the filtered question bank. Omit sections to return all questions."""
    selected = [s.strip() for s in sections.split(",")] if sections else []
    qs = filter_by_sections(selected)
    return QuestionBankResponse(questions=qs, total=len(qs))


# ---------------------------------------------------------------------------
# POST /api/v2/session/start
# ---------------------------------------------------------------------------

@router.post("/session/start", response_model=SessionStartResponse)
async def session_start(body: SessionStartRequest) -> SessionStartResponse:
    """
    Create a new interview session.

    Mode A: selected_sections drives the question set.
    Mode B: followup_queue (question_ids from a prior Mode A analysis) drives it.
    Mode C: selected_sections or all questions if empty.
    """
    session_id = uuid.uuid4()
    now        = datetime.utcnow()

    session = V2Session(
        session_id        = session_id,
        mode              = body.mode,
        respondent_name   = body.respondent_name,
        organization_name = body.organization_name,
        respondent_role   = body.respondent_role,
        organization_unit = body.organization_unit,
        selected_sections = body.selected_sections,
        followup_queue    = body.followup_queue,
        probe_overrides   = body.probe_overrides,
        state             = ConversationState.ASK,
        created_at        = now,
        updated_at        = now,
        expires_at        = store.new_expiry(),
    )

    # Build opening message
    opening_msg = _generator.opening(session)
    session.turns.append(ConversationTurn(role="assistant", text=opening_msg, timestamp=now))

    # Immediately ask the first question
    questions = _get_session_questions(session)
    if questions:
        first_q   = questions[0]
        # Use Phase 1 probe override if available (Mode B follow-up interview)
        if first_q.question_id in session.probe_overrides:
            first_ask = session.probe_overrides[first_q.question_id]
        else:
            first_ask = _generator.ask(session, first_q)
        session.turns.append(ConversationTurn(role="assistant", text=first_ask, timestamp=now))
        opening_text = f"{opening_msg}\n\n{first_ask}"
    else:
        # No questions (e.g., empty sections with no match) — go straight to wrap
        session.state = ConversationState.WRAP
        opening_text  = opening_msg

    store.create(session)

    return SessionStartResponse(
        session_id   = str(session_id),
        mode         = session.mode,
        state        = session.state,
        opening_text = opening_text,
        expires_at   = session.expires_at,
    )


# ---------------------------------------------------------------------------
# POST /api/v2/session/turn
# ---------------------------------------------------------------------------

@router.post("/session/turn", response_model=TurnResponse)
async def session_turn(body: TurnRequest) -> TurnResponse:
    """
    Process one user turn and return the assistant's next message.

    NDA: user_text length is logged but the content is not.
    """
    session = store.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if session.state == ConversationState.WRAP:
        return TurnResponse(
            session_id     = body.session_id,
            state          = ConversationState.WRAP,
            assistant_text = "This interview session is already complete.",
            is_complete    = True,
        )

    now = datetime.utcnow()

    # Record user turn (NDA: content stays in RAM, not logged)
    session.turns.append(ConversationTurn(role="user", text=body.user_text, timestamp=now))

    questions = _get_session_questions(session)
    total     = len(questions)

    # Store extracted answer stub for this question (Chunk 2 fills real extraction)
    if session.current_question_idx < total:
        current_q = questions[session.current_question_idx]
        if current_q.question_id not in session.extracted_answers:
            session.extracted_answers[current_q.question_id] = ExtractedAnswer(
                question_id   = current_q.question_id,
                text_response = body.user_text[:500],  # store first 500 chars
            )

    # Compute transition
    transition = next_state(session, body.user_text, total)

    # Apply transition
    if transition.advance_question:
        session.current_question_idx += 1
        session.clarify_count = 0
    else:
        session.clarify_count += 1

    session.state = transition.next_state

    # Terminal: session complete
    if transition.is_terminal or session.state == ConversationState.WRAP:
        session.state  = ConversationState.WRAP
        wrap_text      = _generator.wrap(session)
        compiled       = _compile_payload(session, questions)

        session.turns.append(ConversationTurn(role="assistant", text=wrap_text, timestamp=now))
        store.update(session)

        return TurnResponse(
            session_id       = body.session_id,
            state            = ConversationState.WRAP,
            assistant_text   = wrap_text,
            is_complete      = True,
            compiled_payload = compiled,
        )

    # Non-terminal: generate next utterance
    assistant_text = _next_utterance(session, questions, now)
    store.update(session)

    return TurnResponse(
        session_id     = body.session_id,
        state          = session.state,
        assistant_text = assistant_text,
        is_complete    = False,
    )


# ---------------------------------------------------------------------------
# GET /api/v2/session/{session_id}
# ---------------------------------------------------------------------------

@router.get("/session/{session_id}", response_model=SessionStatusResponse)
async def session_status(session_id: str) -> SessionStatusResponse:
    """
    Return session status metadata.
    No transcript content is returned (NDA).
    """
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    return SessionStatusResponse(
        session_id         = session_id,
        mode               = session.mode,
        state              = session.state,
        turns_count        = len(session.turns),
        questions_answered = len(session.extracted_answers),
        is_complete        = session.state == ConversationState.WRAP,
        expires_at         = session.expires_at,
    )


# ---------------------------------------------------------------------------
# DELETE /api/v2/session/{session_id}
# ---------------------------------------------------------------------------

@router.delete("/session/{session_id}")
async def session_delete(session_id: str) -> dict:
    """
    Explicitly delete a session. All turn data is erased from RAM.
    NDA: use this to honour data-deletion requests.
    """
    deleted = store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"deleted": True, "session_id": session_id}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_session_questions(session: V2Session) -> List[QuestionBankItem]:
    """
    Return the ordered question list for this session.
    Mode B: questions from followup_queue only (preserves queue order).
    Mode A/C: filtered by selected_sections.
    """
    if session.mode == InterviewMode.B and session.followup_queue:
        qs = [get_question(qid) for qid in session.followup_queue]
        return [q for q in qs if q is not None]
    return filter_by_sections(session.selected_sections)


def _next_utterance(
    session:   V2Session,
    questions: List[QuestionBankItem],
    now:       datetime,
) -> str:
    """Generate and record the assistant's next message."""
    idx = session.current_question_idx

    if idx >= len(questions):
        text = _generator.wrap(session)
    elif session.state == ConversationState.ASK:
        q_id = questions[idx].question_id
        if q_id in session.probe_overrides:
            text = session.probe_overrides[q_id]
        else:
            text = _generator.ask(session, questions[idx])
    elif session.state == ConversationState.CLARIFY:
        text = _generator.clarify(session, questions[idx], session.clarify_count)
    elif session.state == ConversationState.PROBE:
        text = _generator.probe(session, questions[idx])
    else:
        text = _generator.ask(session, questions[idx])

    session.turns.append(ConversationTurn(role="assistant", text=text, timestamp=now))
    return text


def _compile_payload(
    session:   V2Session,
    questions: List[QuestionBankItem],
) -> Dict[str, Any]:
    """
    Compile a v1-compatible AssessmentPayload dict from extracted answers.

    This is the bridge that lets Mode C sessions feed into the Phase 1 analyzer
    (POST /api/analyze-assessment) with zero frontend changes.
    """
    q_responses = []
    for q in questions:
        ans = session.extracted_answers.get(q.question_id)
        q_responses.append({
            "question_id":    q.question_id,
            "category":       q.category,
            "label":          q.label,
            "prompt":         q.prompt,
            "score":          ans.inferred_score if ans else None,
            "typed_response": ans.text_response  if ans else None,
        })

    return {
        "payload_version":   "2.0",
        "respondent_name":   session.respondent_name or "",
        "organization_name": session.organization_name or "",
        "respondent_role":   session.respondent_role,
        "organization_unit": session.organization_unit,
        "selected_sections": session.selected_sections,
        "questions":         q_responses,
        "justifications":    [],
        "source_mode":       session.mode.value,
        "session_id":        str(session.session_id),
    }
