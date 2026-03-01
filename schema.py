"""
schema.py — AHI Diagnostic Reasoning Engine
All Pydantic data contracts. Import these everywhere — never define models inline.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RespondentRole(str, Enum):
    SENIOR_LEADERSHIP = "Senior Leadership"
    TECH_LEAD         = "Tech Lead"
    DATA_LEAD         = "Data Lead"
    OPERATIONS        = "Operations"
    HR                = "HR"
    FINANCE           = "Finance"
    OTHER             = "Other"


class ConfidenceLabel(str, Enum):
    HIGH = "High"
    MED  = "Med"
    LOW  = "Low"


class EvidenceStrengthLabel(str, Enum):
    NONE     = "None"
    WEAK     = "Weak"
    MODERATE = "Moderate"
    STRONG   = "Strong"


# ---------------------------------------------------------------------------
# Inbound payload models
# ---------------------------------------------------------------------------

class TaggedJustification(BaseModel):
    """One tagged note attached to a specific question or category."""
    category:  str            = Field(..., max_length=100)
    tag_id:    str            = Field(..., max_length=50)
    tag_label: Optional[str]  = Field(None, max_length=200)
    text:      Optional[str]  = Field(None, max_length=3000)
    has_audio: bool           = False

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip() or None
        return v

    @field_validator("category", "tag_id", mode="before")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip()


class QuestionResponse(BaseModel):
    """A single question + its Likert score + optional typed response."""
    question_id:    str           = Field(..., max_length=50)
    category:       str           = Field(..., max_length=100)
    label:          str           = Field(..., max_length=200)
    prompt:         str           = Field(..., max_length=500)
    score:          Optional[int] = Field(None, ge=1, le=5)
    typed_response: Optional[str] = Field(None, max_length=3000)

    @field_validator("typed_response", mode="before")
    @classmethod
    def strip_typed(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip() or None
        return v


class AssessmentPayload(BaseModel):
    """
    Top-level inbound payload from the frontend.
    Extended from original shape to include role, org_unit, and versioning.
    """
    payload_version:   str                    = Field("1.0", max_length=10)
    respondent_name:   str                    = Field(...,   max_length=150)
    organization_name: str                    = Field(...,   max_length=150)
    respondent_role:   Optional[RespondentRole] = None
    organization_unit: Optional[str]          = Field(None, max_length=150)
    selected_sections: List[str]              = Field(default_factory=list)
    questions:         List[QuestionResponse]
    justifications:    List[TaggedJustification] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_has_questions(self) -> "AssessmentPayload":
        if not self.questions:
            raise ValueError("Payload must contain at least one question response.")
        return self

    @field_validator("respondent_name", "organization_name", mode="before")
    @classmethod
    def strip_fields(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# Outbound result models
# ---------------------------------------------------------------------------

class PerQuestionResult(BaseModel):
    """Analysis result for one question."""
    question_id:              str
    category:                 str
    label:                    str
    self_score:               Optional[int]
    inferred_stage:           str
    confidence:               float
    confidence_label:         ConfidenceLabel
    evidence_strength:        int             # 0–3
    evidence_strength_label:  EvidenceStrengthLabel
    has_supporting_audio:     bool
    mentions_metric:          bool
    mentions_owner:           bool
    mentions_cadence:         bool
    mentions_system:          bool
    red_flags:                List[str]
    recommended_followups:    List[str]
    supporting_text_excerpt:  Optional[str]
    evidence_id:              Optional[str] = None  # stable UUID for traceability


class DimensionSummary(BaseModel):
    """Rolled-up analysis for one assessment category."""
    category:         str
    avg_score:        Optional[float]
    avg_confidence:   float
    confidence_label: ConfidenceLabel
    summary_flags:    List[str]
    question_count:   int


class OverallAssessment(BaseModel):
    composite_score:          float
    maturity_stage:           str
    needs_human_followup:     bool
    assessment_quality_note:  str


class HybridAnalystSummary(BaseModel):
    """
    Statistical benchmarking block.
    Only present when benchmark data contains N >= MIN_BENCHMARK_SAMPLE
    for the respondent's role.
    """
    role_compared_to:        Optional[str]
    role_avg_composite:      Optional[float]
    respondent_zscore:       Optional[float]
    zscore_interpretation:   Optional[str]
    perception_gaps:         List[str]      # e.g. ["Data Readiness: Tech Lead 2.1 vs Leadership 4.3"]
    outlier_flags:           List[str]
    benchmark_note:          str


class FollowupQueueItem(BaseModel):
    """
    One item in the follow-up interview queue.
    Generated from per-question analysis results — drives Mode B sessions.
    """
    question_id:             str
    category:                str
    label:                   str
    priority:                str           # "critical" | "high" | "medium"
    reason:                  List[str]     # red_flag strings that triggered this item
    probe:                   str           # primary consultant probe text
    prior_score:             Optional[int]
    confidence:              float
    supporting_text_excerpt: Optional[str]
    evidence_id:             Optional[str] = None  # matches PerQuestionResult.evidence_id


class AnalysisResponse(BaseModel):
    """Full outbound response from /api/analyze-assessment."""
    submission_id:     Optional[str] = None  # stable ID for follow-up sessions and DB queries
    respondent_name:   str
    organization_name: str
    phase:             str = "phase_1_structured_analyzer"
    overall:           OverallAssessment
    dimensions:        List[DimensionSummary]
    per_question:      List[PerQuestionResult]
    top_blockers:      List[str]
    quick_wins:        List[str]
    next_best_actions: List[str]
    followup_queue:    List[FollowupQueueItem] = Field(default_factory=list)
    hybrid_analyst:    Optional[HybridAnalystSummary] = None


# ---------------------------------------------------------------------------
# Example payload (served by GET /api/schema/example-payload)
# ---------------------------------------------------------------------------

EXAMPLE_PAYLOAD: dict = {
    "payload_version": "1.0",
    "respondent_name": "Alex Rivera",
    "organization_name": "FinCo Global",
    "respondent_role": "Tech Lead",
    "organization_unit": "Enterprise Data Platform",
    "selected_sections": ["tech", "data", "leadership"],
    "questions": [
        {
            "question_id": "L1",
            "category": "Leadership & Vision",
            "label": "Strategic AI Vision",
            "prompt": "Our organization has a clear and compelling AI vision and roadmap in place.",
            "score": 4,
            "typed_response": None
        },
        {
            "question_id": "D1",
            "category": "Data Readiness",
            "label": "Data Quality Ownership",
            "prompt": "We have clearly assigned data quality ownership and a formal data dictionary.",
            "score": 2,
            "typed_response": "No formal data dictionary yet. Quality checks exist in a few pipelines."
        },
        {
            "question_id": "G1",
            "category": "Governance Readiness",
            "label": "AI Policies and Review",
            "prompt": "Formal AI usage and governance policies exist and are reviewed regularly.",
            "score": 4,
            "typed_response": "AI Policy v2.1 approved by Risk Committee Jan 2026; monthly compliance reviews."
        },
    ],
    "justifications": [
        {
            "category": "Data Readiness",
            "tag_id": "D1",
            "tag_label": "D1 - Data Quality Ownership",
            "text": "We track data issues ad hoc in Jira. No assigned data owners per domain.",
            "has_audio": False
        }
    ]
}
