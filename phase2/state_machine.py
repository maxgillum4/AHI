"""
phase2/state_machine.py — Interview state machine.

State flow:
    ASK → user answers
        → has_specifics(reply) OR clarify_count >= max_clarify  → advance → ASK | WRAP
        → vague reply + clarify budget remaining                → CLARIFY
        → is_skip                                               → advance → ASK | WRAP

    CLARIFY → user answers  (same evaluation as above)

    WRAP (terminal) — populated by api.py wrap handler

SCORE is an internal logical step, not an interactive state.
When we decide the response is sufficient, the question is advanced
and the session wraps or proceeds to the next question.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schemas import ConversationState, V2Session

# ---------------------------------------------------------------------------
# Skip vocabulary
# ---------------------------------------------------------------------------

SKIP_SIGNALS = frozenset([
    "skip", "pass", "next", "move on", "not sure",
    "don't know", "i don't know", "i don't own",
    "not my area", "no idea", "n/a", "na",
])


def is_skip(text: str) -> bool:
    """True if the user's text matches a skip / pass signal."""
    normalized = text.lower().strip().rstrip(".")
    return normalized in SKIP_SIGNALS or any(
        normalized.startswith(sig) for sig in SKIP_SIGNALS if len(sig) > 4
    )


# ---------------------------------------------------------------------------
# Specificity detection — self-contained, no dependency on analyzer.py
# ---------------------------------------------------------------------------

# Signals that indicate a response contains concrete, actionable evidence.
# Each category is checked independently; one hit is enough to consider
# the response specific.
_SPECIFICS_VOCABULARY: dict[str, list[str]] = {
    "ownership": [
        "owns", "owner", "responsible for", "accountable", "cto", "cdo",
        "cio", "head of", "director of", "vp of", "lead", "i am", "my team",
        "our team", "we assigned",
    ],
    "metrics": [
        "%", "percent", "kpi", "roi", "metric", "measure", "target",
        "$", "revenue", "cost", "rate", "score", "number", "benchmark",
        "quarterly target", "baseline",
    ],
    "cadence": [
        "weekly", "monthly", "quarterly", "annually", "daily", "every week",
        "cadence", "reviewed", "sprint", "biweekly", "each quarter",
        "review cycle",
    ],
    "system": [
        "platform", "tool", "system", "software", "dashboard", "database",
        "pipeline", "api", "model", "deployed", "using", "we use", "runs on",
    ],
    "specificity": [
        "specifically", "for example", "such as", "we have", "implemented",
        "launched", "completed", "approved", "in place", "we track",
        "we report", "last quarter", "this year", "since",
    ],
}


def has_specifics(text: str) -> bool:
    """
    True if the reply contains at least one concrete evidence signal.

    A single category hit is sufficient — we're checking for the presence
    of any operational anchor (owner, KPI, system, cadence, or concrete example),
    not requiring all of them at once.
    """
    if not text or len(text.split()) < 5:
        # Too short to contain useful specifics regardless of content
        return False
    lower = text.lower()
    return any(
        any(kw in lower for kw in signals)
        for signals in _SPECIFICS_VOCABULARY.values()
    )


def missing_signals(text: str) -> list[str]:
    """
    Return the signal categories absent from the text.

    Complement of has_specifics — tells callers which specific evidence type
    (ownership, metrics, cadence, system, specificity) to ask for next.
    Returns all categories when text is too short to evaluate.
    """
    if not text or len(text.split()) < 5:
        return list(_SPECIFICS_VOCABULARY.keys())
    lower = text.lower()
    return [
        cat for cat, signals in _SPECIFICS_VOCABULARY.items()
        if not any(kw in lower for kw in signals)
    ]


# ---------------------------------------------------------------------------
# Transition result
# ---------------------------------------------------------------------------

@dataclass
class TransitionResult:
    next_state:       ConversationState
    advance_question: bool   # True → increment current_question_idx
    is_terminal:      bool   # True → session is done (WRAP)


# ---------------------------------------------------------------------------
# Boundary check
# ---------------------------------------------------------------------------

def should_wrap(session: V2Session, total_questions: int) -> bool:
    """True if the session has exhausted all questions."""
    return session.current_question_idx >= total_questions


# ---------------------------------------------------------------------------
# Main transition function
# ---------------------------------------------------------------------------

def next_state(
    session:         V2Session,
    user_text:       str,
    total_questions: int,
) -> TransitionResult:
    """
    Compute the next conversation state after the user's turn.

    Decision tree:
      1. Skip signal  → advance question, wrap if last
      2. Response has specifics OR clarify budget exhausted  → advance, wrap if last
      3. Vague + budget remaining  → CLARIFY (same question)
    """
    # 1. Skip
    if is_skip(user_text):
        return _advance(session, total_questions)

    # 2. Sufficient response or clarify budget exhausted
    if has_specifics(user_text) or session.clarify_count >= session.max_clarify:
        return _advance(session, total_questions)

    # 3. Still vague — ask for clarification
    return TransitionResult(
        next_state       = ConversationState.CLARIFY,
        advance_question = False,
        is_terminal      = False,
    )


def _advance(session: V2Session, total_questions: int) -> TransitionResult:
    """Advance to the next question; wrap if at the end."""
    next_idx = session.current_question_idx + 1
    is_done  = next_idx >= total_questions
    return TransitionResult(
        next_state       = ConversationState.WRAP if is_done else ConversationState.ASK,
        advance_question = True,
        is_terminal      = is_done,
    )
