"""
phase2/generation/claude_generator.py — Claude API generator stub.

Requires: ANTHROPIC_API_KEY environment variable.
Activated by: GENERATION_MODE=claude or GENERATION_MODE=hybrid

Chunk 1: raises NotImplementedError — implemented in Chunk 3.

Design intent (Chunk 3):
  - Maintains a rolling system prompt that includes session context, prior turns,
    and extracted evidence signals.
  - Generates contextual, adaptive questions — not just templates.
  - Falls back to TemplateGenerator on any API error (hybrid mode).
  - Never logs transcript content — only logs token counts and latency.
"""

from __future__ import annotations

from typing import Optional

from ..schemas import QuestionBankItem, V2Session
from .base import TurnGenerator


class ClaudeGenerator(TurnGenerator):
    """
    Stub. Chunk 3 will implement the Anthropic Claude API integration.
    """

    def __init__(self) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "anthropic package required for ClaudeGenerator. "
                "Install with: pip install anthropic"
            ) from exc
        # Chunk 3: initialize client, load system prompt template
        raise NotImplementedError(
            "ClaudeGenerator is not yet implemented (scheduled for Chunk 3). "
            "Set GENERATION_MODE=template to use the deterministic fallback."
        )

    def opening(self, session: V2Session) -> str:
        raise NotImplementedError("ClaudeGenerator not yet implemented (Chunk 3)")

    def ask(self, session: V2Session, question: QuestionBankItem) -> str:
        raise NotImplementedError("ClaudeGenerator not yet implemented (Chunk 3)")

    def clarify(
        self,
        session:         V2Session,
        question:        QuestionBankItem,
        clarify_attempt: int,
    ) -> str:
        raise NotImplementedError("ClaudeGenerator not yet implemented (Chunk 3)")

    def probe(
        self,
        session:       V2Session,
        question:      QuestionBankItem,
        probe_context: Optional[str] = None,
    ) -> str:
        raise NotImplementedError("ClaudeGenerator not yet implemented (Chunk 3)")

    def wrap(self, session: V2Session) -> str:
        raise NotImplementedError("ClaudeGenerator not yet implemented (Chunk 3)")
