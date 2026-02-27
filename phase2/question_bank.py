"""
phase2/question_bank.py — Canonical question definitions.

Single source of truth for all interview questions, migrated from v1 HTML (app.py).
Sections map to the data-sections attributes used in the frontend form.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .schemas import QuestionBankItem

# ---------------------------------------------------------------------------
# Master question list — order = interview order
# sections = which selected_section keys make this question visible
# ---------------------------------------------------------------------------

QUESTIONS: List[QuestionBankItem] = [

    # ── Leadership & Vision ──────────────────────────────────────────────────
    QuestionBankItem(
        question_id="L1",
        category="Leadership & Vision",
        label="Strategic AI Vision",
        prompt="Our organization has a clear and compelling AI vision and roadmap in place.",
        question_type="likert",
        sections=["leadership"],
    ),
    QuestionBankItem(
        question_id="L2",
        category="Leadership & Vision",
        label="Corporate Strategy Alignment",
        prompt="AI objectives are explicitly aligned with our primary corporate strategy.",
        question_type="likert",
        sections=["leadership"],
    ),
    QuestionBankItem(
        question_id="L3",
        category="Leadership & Vision",
        label="AI Enterprise Metrics",
        prompt="How mature are the KPIs used to track AI investment value and business ROI?",
        question_type="likert",
        sections=["leadership"],
    ),
    QuestionBankItem(
        question_id="L_Risk",
        category="Leadership & Vision",
        label="AI Risk Appetite",
        prompt="What level of AI risk is leadership willing to accept for competitive gain?",
        question_type="likert",
        sections=["leadership"],
    ),
    QuestionBankItem(
        question_id="Q_Decision",
        category="Leadership & Vision",
        label="AI Decision Ownership",
        prompt="Who holds final accountability for AI investment and deployment decisions?",
        question_type="qualitative",
        sections=["leadership", "tech"],
    ),

    # ── Ways of Working ──────────────────────────────────────────────────────
    QuestionBankItem(
        question_id="W1",
        category="Ways of Working",
        label="Technology Designed for Business",
        prompt="There is a strong, collaborative connection between business and technical teams.",
        question_type="likert",
        sections=["leadership", "tech", "data"],
    ),
    QuestionBankItem(
        question_id="W_Conflict",
        category="Ways of Working",
        label="Conflict Resolution",
        prompt="How effective is the process for resolving disagreements on AI direction?",
        question_type="likert",
        sections=["leadership", "tech"],
    ),
    QuestionBankItem(
        question_id="W3",
        category="Ways of Working",
        label="Utilize AI-Driven Insights",
        prompt="How deeply are AI-driven insights integrated into daily decision-making?",
        question_type="likert",
        sections=["leadership", "tech"],
    ),

    # ── Culture & Workforce ──────────────────────────────────────────────────
    QuestionBankItem(
        question_id="C1",
        category="Culture & Workforce",
        label="Organization Aligns to Business Priorities",
        prompt="The organization aligns quickly to business transformation and AI priorities.",
        question_type="likert",
        sections=["hr"],
    ),
    QuestionBankItem(
        question_id="C3",
        category="Culture & Workforce",
        label="Employees Willingness to Embrace AI",
        prompt="Employees are willing and excited to embrace AI tools in their daily work.",
        question_type="likert",
        sections=["hr"],
    ),
    QuestionBankItem(
        question_id="C_Fatigue",
        category="Culture & Workforce",
        label="Transformation Legacy",
        prompt="How well has the organization historically managed large-scale technological shifts?",
        question_type="likert",
        sections=["hr"],
    ),
    QuestionBankItem(
        question_id="Q_Concerns",
        category="Culture & Workforce",
        label="Employee Concerns",
        prompt="What are the primary concerns regarding AI adoption today?",
        question_type="qualitative",
        sections=["hr", "leadership"],
    ),

    # ── Governance Readiness ─────────────────────────────────────────────────
    QuestionBankItem(
        question_id="G1",
        category="Governance Readiness",
        label="Solid Governance Structure",
        prompt="We have a robust AI governance and ethics framework currently active.",
        question_type="likert",
        sections=["leadership", "tech"],
    ),
    QuestionBankItem(
        question_id="G4",
        category="Governance Readiness",
        label="Effective Risk Mitigation",
        prompt="Our processes identify bias, privacy, and security risks in AI models.",
        question_type="likert",
        sections=["leadership", "tech"],
    ),
    QuestionBankItem(
        question_id="G_Shadow",
        category="Governance Readiness",
        label="Shadow AI Confidence",
        prompt="Confidence that AI usage is restricted to approved platforms.",
        question_type="likert",
        sections=["leadership", "tech"],
    ),

    # ── Technology Readiness ─────────────────────────────────────────────────
    QuestionBankItem(
        question_id="T1",
        category="Technology Readiness",
        label="Modern Cloud Infrastructure",
        prompt="Readiness to support high-performance AI model deployment.",
        question_type="likert",
        sections=["tech"],
    ),
    QuestionBankItem(
        question_id="T2",
        category="Technology Readiness",
        label="Core Systems AI Ready",
        prompt="ERP/CRM readiness to serve as an enterprise AI foundation.",
        question_type="likert",
        sections=["tech"],
    ),
    QuestionBankItem(
        question_id="T4",
        category="Technology Readiness",
        label="ML Ops Maturity",
        prompt="Maturity of AI platform monitoring and automated deployment.",
        question_type="likert",
        sections=["tech"],
    ),
    QuestionBankItem(
        question_id="T5",
        category="Technology Readiness",
        label="Security Architecture",
        prompt="Enterprise architecture supports modern zero-trust AI security needs.",
        question_type="likert",
        sections=["tech"],
    ),

    # ── Data Readiness ───────────────────────────────────────────────────────
    QuestionBankItem(
        question_id="D1",
        category="Data Readiness",
        label="Data structured & clean",
        prompt="Data is structured and clean across primary business domains.",
        question_type="likert",
        sections=["data", "tech"],
    ),
    QuestionBankItem(
        question_id="D2",
        category="Data Readiness",
        label="Data integrated for AI",
        prompt="Cross-functional data is formatted and available for model training.",
        question_type="likert",
        sections=["data", "tech"],
    ),
    QuestionBankItem(
        question_id="D3",
        category="Data Readiness",
        label="Data Dictionary and Ownership",
        prompt="We have clear data dictionaries and assigned domain ownership.",
        question_type="likert",
        sections=["data", "tech"],
    ),
    QuestionBankItem(
        question_id="Q_Vision",
        category="Data Readiness",
        label="Future-State Vision",
        prompt="What is the desired day-to-day impact of AI on the organization in two years?",
        question_type="qualitative",
        sections=["leadership", "tech", "data", "hr"],
    ),
]

# ---------------------------------------------------------------------------
# Indexes for O(1) lookup
# ---------------------------------------------------------------------------

_BY_ID: Dict[str, QuestionBankItem] = {q.question_id: q for q in QUESTIONS}


def get_question(question_id: str) -> Optional[QuestionBankItem]:
    """Return a question by ID, or None."""
    return _BY_ID.get(question_id)


def filter_by_sections(selected_sections: List[str]) -> List[QuestionBankItem]:
    """
    Return questions that appear in ANY of the selected sections (de-duped,
    preserving canonical order). If selected_sections is empty, return all.
    """
    if not selected_sections:
        return QUESTIONS[:]
    sec_set = {s.lower().strip() for s in selected_sections}
    seen: set = set()
    result = []
    for q in QUESTIONS:
        if q.question_id not in seen and sec_set.intersection(q.sections):
            seen.add(q.question_id)
            result.append(q)
    return result
