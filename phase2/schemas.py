"""
phase2/schemas.py — Phase 2 Pydantic contracts.
All Phase 2 data models. Import from here — never define inline.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InterviewMode(str, Enum):
    A = "A"   # Enhanced Form — structured form, richer report + followup_queue
    B = "B"   # Follow-up Interview — chat seeded from Mode A followup_queue
    C = "C"   # Full Interview — no form, fully conversational end-to-end


class ConversationState(str, Enum):
    ASK     = "ASK"     # Presenting a new question for the first time
    CLARIFY = "CLARIFY" # Asking for elaboration on the same topic
    PROBE   = "PROBE"   # Drilling into a red flag or identified gap
    SCORE   = "SCORE"   # Internally inferring Likert score (not user-facing)
    WRAP    = "WRAP"    # Session complete, AssessmentPayload compiled


# ---------------------------------------------------------------------------
# Session models
# ---------------------------------------------------------------------------

class ConversationTurn(BaseModel):
    role:      str       # "assistant" | "user"
    text:      str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExtractedAnswer(BaseModel):
    """What the engine extracted from the user's conversational response."""
    question_id:    str
    inferred_score: Optional[int] = Field(None, ge=1, le=5)
    text_response:  Optional[str] = None
    confidence:     float         = 0.0   # 0.0–1.0 extraction confidence (Chunk 2)


class V2Session(BaseModel):
    session_id:        UUID
    mode:              InterviewMode
    respondent_name:   Optional[str] = None
    organization_name: Optional[str] = None
    respondent_role:   Optional[str] = None
    organization_unit: Optional[str] = None
    selected_sections: List[str]     = Field(default_factory=list)

    state:                ConversationState = ConversationState.ASK
    current_question_idx: int               = 0
    clarify_count:        int               = 0   # probes on current question
    max_clarify:          int               = 2   # stop probing after this many

    followup_queue:    List[str]                    = Field(default_factory=list)
    probe_overrides:   Dict[str, str]               = Field(default_factory=dict)  # question_id -> probe text from Phase 1
    turns:             List[ConversationTurn]        = Field(default_factory=list)
    extracted_answers: Dict[str, ExtractedAnswer]   = Field(default_factory=dict)

    # Follow-up session tracking (Chunk 2)
    # Set when the session is started from a persisted submission via /followup/start.
    # Drives the wrap pipeline to patch DB + re-run Phase 1.
    source_submission_id: Optional[str] = None
    source_question_id:   Optional[str] = None
    source_evidence_id:   Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=datetime.utcnow)  # set by store


# ---------------------------------------------------------------------------
# Question bank item
# ---------------------------------------------------------------------------

class QuestionBankItem(BaseModel):
    question_id:   str
    category:      str
    label:         str
    prompt:        str
    question_type: str         # "likert" | "qualitative"
    sections:      List[str]   # which selected_section keys include this question


class QuestionBankResponse(BaseModel):
    questions: List[QuestionBankItem]
    total:     int


# ---------------------------------------------------------------------------
# Request / Response contracts
# ---------------------------------------------------------------------------

class SessionStartRequest(BaseModel):
    mode:              InterviewMode
    respondent_name:   Optional[str] = Field(None, max_length=150)
    organization_name: Optional[str] = Field(None, max_length=150)
    respondent_role:   Optional[str] = Field(None, max_length=100)
    organization_unit: Optional[str] = Field(None, max_length=150)
    selected_sections: List[str]     = Field(default_factory=list)
    # Mode B: seed the followup queue from a prior Mode A analysis
    followup_queue:    List[str]     = Field(default_factory=list)
    # Optional: override the generated probe text with Phase 1 consultant probes
    probe_overrides:   Dict[str, str] = Field(default_factory=dict)  # question_id -> probe text


class SessionStartResponse(BaseModel):
    session_id:   str
    mode:         InterviewMode
    state:        ConversationState
    opening_text: str
    expires_at:   datetime


class TurnRequest(BaseModel):
    session_id: str
    user_text:  str = Field(..., max_length=5000)


class TurnResponse(BaseModel):
    session_id:       str
    state:            ConversationState
    assistant_text:   str
    is_complete:      bool                    = False
    # Populated only when is_complete=True
    compiled_payload:    Optional[Dict[str, Any]] = None
    # Populated only for follow-up sessions (source_submission_id set) on wrap
    refreshed_analysis:  Optional[Dict[str, Any]] = None


class SessionStatusResponse(BaseModel):
    session_id:         str
    mode:               InterviewMode
    state:              ConversationState
    turns_count:        int
    questions_answered: int
    is_complete:        bool
    expires_at:         datetime


# ---------------------------------------------------------------------------
# Follow-up session request/response (Chunk 2)
# ---------------------------------------------------------------------------

class FollowupStartRequest(BaseModel):
    """
    Start a bounded follow-up interview from a persisted Phase 1 submission.

    The session will be tightly scoped to the single flagged question identified
    by question_id. On wrap, the persisted submission is patched and re-analyzed.
    """
    submission_id:    str = Field(..., max_length=36)
    question_id:      str = Field(..., max_length=50)
    probe_override:   Optional[str] = Field(None, max_length=1000)
    respondent_name:  Optional[str] = Field(None, max_length=150)
    organization_name: Optional[str] = Field(None, max_length=150)
