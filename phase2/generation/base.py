"""
phase2/generation/base.py — TurnGenerator abstract interface.

All generators (template, Claude, hybrid) must implement this contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..schemas import QuestionBankItem, V2Session


class TurnGenerator(ABC):
    """
    Generates the assistant's next utterance given session state + current question.

    Implementations:
      - TemplateGenerator (Chunk 1) — deterministic, no LLM, McKinsey voice
      - ClaudeGenerator   (Chunk 3) — Claude API, contextual and adaptive
    """

    @abstractmethod
    def opening(self, session: V2Session) -> str:
        """First message when session starts — introduce the interview."""
        ...

    @abstractmethod
    def ask(self, session: V2Session, question: QuestionBankItem) -> str:
        """Present a question for the first time."""
        ...

    @abstractmethod
    def clarify(
        self,
        session:         V2Session,
        question:        QuestionBankItem,
        clarify_attempt: int,
    ) -> str:
        """Follow up for elaboration (attempt 1 or 2)."""
        ...

    @abstractmethod
    def probe(
        self,
        session:       V2Session,
        question:      QuestionBankItem,
        probe_context: Optional[str] = None,
    ) -> str:
        """Drill into a specific gap or concern."""
        ...

    @abstractmethod
    def wrap(self, session: V2Session) -> str:
        """Closing message when the interview is complete."""
        ...
