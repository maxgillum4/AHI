"""
phase2/generation/template_generator.py — Deterministic template-based generator.

No LLM dependency. Production-ready fallback.
Voice: McKinsey Partner — clinical, specific, ROI-focused. No AI hype.

Used when GENERATION_MODE=template (default).
"""

from __future__ import annotations

import random
from typing import Optional

from ..schemas import QuestionBankItem, V2Session
from .base import TurnGenerator


class TemplateGenerator(TurnGenerator):
    """Rule-based, stateless response generator."""

    # -----------------------------------------------------------------------
    # Opening
    # -----------------------------------------------------------------------

    def opening(self, session: V2Session) -> str:
        name = session.respondent_name or "there"
        org  = session.organization_name or "your organization"
        mode_notes = {
            "A": "",
            "B": (
                " We'll focus specifically on the areas that surfaced as highest priority "
                "in your initial assessment."
            ),
            "C": (
                " We'll work through your organization's AI readiness together — "
                "no form required, just a conversation."
            ),
        }
        mode_note = mode_notes.get(session.mode.value, "")
        return (
            f"Thank you for your time today, {name}. "
            f"I'll be asking about {org}'s AI readiness across several dimensions.{mode_note} "
            "There are no right or wrong answers — I'm looking for honest, specific context. "
            "You can say 'skip' at any point to move to the next topic. Let's begin."
        )

    # -----------------------------------------------------------------------
    # Ask
    # -----------------------------------------------------------------------

    _CATEGORY_INTRO: dict[str, str] = {
        "Leadership & Vision":  "Starting with leadership and strategic direction. ",
        "Ways of Working":      "Moving to operational dynamics. ",
        "Culture & Workforce":  "Now, culture and workforce readiness. ",
        "Governance Readiness": "Turning to governance and risk controls. ",
        "Technology Readiness": "On to technology infrastructure. ",
        "Data Readiness":       "Finally, data assets and quality. ",
    }

    def ask(self, session: V2Session, question: QuestionBankItem) -> str:
        # Use category intro only on the first question of each category
        seen_cats = {
            session.extracted_answers[qid].question_id
            for qid in session.extracted_answers
        }
        # Determine if this is the first question in this category
        intro = ""
        first_in_cat = not any(
            True
            for turn in session.turns
            if question.category in turn.text and turn.role == "assistant"
        )
        if first_in_cat:
            intro = self._CATEGORY_INTRO.get(question.category, "")

        if question.question_type == "qualitative":
            return f"{intro}{question.prompt}"
        return (
            f"{intro}On a scale of 1 (strongly disagree) to 5 (strongly agree): "
            f"{question.prompt}"
        )

    # -----------------------------------------------------------------------
    # Clarify
    # -----------------------------------------------------------------------

    _CLARIFY_BANK_1 = [
        "Can you give me a concrete example that illustrates where things stand today?",
        "What does that look like in practice — any specific initiatives or metrics?",
        "Help me understand the current reality. Is this aspirational, or actively operating?",
        "What evidence would a skeptical board member see that confirms this rating?",
    ]

    _CLARIFY_BANK_2 = [
        "Who specifically owns this, and how is progress measured?",
        "What's the biggest barrier to moving this forward right now?",
        "When did this become a priority, and what triggered it?",
        "If this were rated 1 point lower, what would look different?",
    ]

    # Priority order for which missing signal to ask about first
    _SIGNAL_PRIORITY = ["ownership", "metrics", "cadence", "system", "specificity"]

    # Targeted one-shot questions per missing signal category
    _SIGNAL_QUESTIONS: dict[str, str] = {
        "ownership":   "Who specifically owns this — a named individual or team with clear accountability?",
        "metrics":     "What KPI or metric tracks progress here, and what does that number look like today?",
        "cadence":     "How frequently is this reviewed, and who's in the room when it is?",
        "system":      "Which platform, tool, or system actually supports this today — by name?",
        "specificity": "Can you give me one concrete example of this in practice from the last 90 days?",
    }

    def clarify(
        self,
        session:         V2Session,
        question:        QuestionBankItem,
        clarify_attempt: int,
    ) -> str:
        from ..state_machine import missing_signals

        # Pull the last user turn to diagnose what's missing
        last_user = next(
            (t.text for t in reversed(session.turns) if t.role == "user"), ""
        )
        if last_user:
            missing = missing_signals(last_user)
            for sig in self._SIGNAL_PRIORITY:
                if sig in missing:
                    return self._SIGNAL_QUESTIONS[sig]

        # Fallback: generic bank (nothing clearly missing, or text too short)
        bank = self._CLARIFY_BANK_2 if clarify_attempt >= 2 else self._CLARIFY_BANK_1
        return random.choice(bank)

    # -----------------------------------------------------------------------
    # Probe
    # -----------------------------------------------------------------------

    _PROBE_BANKS: dict[str, list[str]] = {
        "Leadership & Vision": [
            "Who has the authority to stop an AI initiative that's underperforming, "
            "and has that authority ever been exercised?",
            "How does AI investment get prioritized against competing capital demands?",
            "Walk me through how the current AI roadmap was created and who approved it.",
        ],
        "Ways of Working": [
            "Walk me through a recent situation where a cross-functional AI decision was made. "
            "Who was in the room, and who made the final call?",
            "When business and tech disagree on AI direction, what's the tiebreaker?",
            "Describe the last time an AI initiative stalled due to organizational friction.",
        ],
        "Culture & Workforce": [
            "What specific, visible actions has leadership taken to address AI-related employee concerns?",
            "Have you seen shadow AI usage emerge — and how was it handled?",
            "Which part of the organization is most resistant to AI adoption, and why?",
        ],
        "Governance Readiness": [
            "Has your governance process ever stopped or significantly altered an AI deployment? "
            "Walk me through that situation.",
            "Who reviews AI model outputs for bias or unintended consequences, "
            "and how often does that review happen?",
            "What would trigger an immediate halt to an AI system in production?",
        ],
        "Technology Readiness": [
            "What's your current inference latency for your most performance-sensitive AI workload?",
            "Have you experienced any AI-related security incidents? "
            "How were they detected and resolved?",
            "Describe your MLOps pipeline — from model training to production monitoring.",
        ],
        "Data Readiness": [
            "Which business domain has the cleanest, most accessible data today, and what makes it that way?",
            "How long would it take to assemble a labeled training dataset for a net-new use case?",
            "Who is responsible when a model degrades because of data quality drift?",
        ],
    }

    _PROBE_DEFAULT = [
        "Can you walk me through the last time this was formally reviewed or audited?",
        "What would need to change for you to rate this significantly higher in 12 months?",
        "Where does this rank in terms of leadership's current AI priorities?",
    ]

    def probe(
        self,
        session:       V2Session,
        question:      QuestionBankItem,
        probe_context: Optional[str] = None,
    ) -> str:
        bank = self._PROBE_BANKS.get(question.category, self._PROBE_DEFAULT)
        return random.choice(bank)

    # -----------------------------------------------------------------------
    # Wrap
    # -----------------------------------------------------------------------

    def wrap(self, session: V2Session) -> str:
        name = session.respondent_name or "you"
        n    = len(session.extracted_answers)
        return (
            f"Thank you, {name} — that covers the key dimensions. "
            f"I've captured your perspective across {n} topic{'s' if n != 1 else ''}. "
            "Your consultant will review the full analysis and follow up with prioritized recommendations. "
            "This session is complete."
        )
