"""
phase2/state_machine.py — Interview state machine interfaces.

Chunk 1: type definitions, stop-condition helpers, and a simplified linear
transition that advances one question per user turn.

Chunk 2 will replace next_state() with real evidence extraction, score
inference, and adaptive probing logic.

State flow (Chunk 1 simplified):
    ASK -> user answers -> ASK (next question) -> ... -> WRAP (terminal)
    Any state + skip signal -> ASK (next question) or WRAP

Full state enum (structure preserved for Chunk 2 upgrades):
    ASK     — presenting a question
    CLARIFY — requesting elaboration on the same question
    PROBE   — drilling into a red flag or gap
    SCORE   — internal scoring inference (non-interactive)
    WRAP    — session complete
"""

from __future__ import annotations

from dataclasses import dataclass

from .schemas import ConversationState, V2Session

# ---------------------------------------------------------------------------
# Stop-condition vocabulary
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
# Main transition function (Chunk 1: simplified linear)
# ---------------------------------------------------------------------------

def next_state(
    session:         V2Session,
    user_text:       str,
    total_questions: int,
) -> TransitionResult:
    """
    Compute the next conversation state after the user's turn.

    Chunk 1 logic: every user response advances to the next question.
    Chunk 2 will augment this with evidence extraction, score inference,
    and context-sensitive CLARIFY / PROBE branching.
    """
    next_idx = session.current_question_idx + 1
    is_done  = next_idx >= total_questions

    return TransitionResult(
        next_state       = ConversationState.WRAP if is_done else ConversationState.ASK,
        advance_question = True,
        is_terminal      = is_done,
    )
