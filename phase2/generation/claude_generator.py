"""
phase2/generation/claude_generator.py — Claude-powered follow-up generator.

Activated by: GENERATION_MODE=claude or GENERATION_MODE=hybrid
Requires:     ANTHROPIC_API_KEY environment variable

Design:
  - Tightly bounded to the flagged issue — never drifts off-topic
  - Uses claude-haiku for speed and cost efficiency
  - Fails gracefully: all methods fall back to TemplateGenerator on any API error
  - Never logs transcript content (only token counts)
  - Opening and Ask delegate to TemplateGenerator (templates are perfectly adequate)
  - Clarify and Wrap are where live generation adds the most value

NDA: no session transcript content is sent to Claude beyond what is
     already in the session's turns (which are RAM-only for the session TTL).
"""

from __future__ import annotations

import os
from typing import List, Optional

from ..schemas import QuestionBankItem, V2Session
from .base import TurnGenerator
from .template_generator import TemplateGenerator


class ClaudeGenerator(TurnGenerator):
    """
    Claude Haiku-powered generator with TemplateGenerator fallback on every method.

    System prompt constrains Claude to:
    - McKinsey consultant persona
    - Bounded to the specific flagged question
    - Demand concrete specifics (owner / KPI / system / cadence)
    - Maximum 2 sentences
    - No AI hype, no disclosure of scoring methodology
    """

    _SYSTEM = (
        "You are a Senior AI Strategy Consultant conducting a brief, targeted "
        "follow-up interview. A specific concern was flagged in an AI maturity "
        "assessment and you are probing it for concrete evidence. "
        "Rules: stay strictly on the flagged topic; ask for named owners, "
        "quantified KPIs, specific systems, or review cadence; respond in at "
        "most 2 sentences; clinical and direct tone; no AI hype language; "
        "never disclose internal assessment scores or methodology."
    )

    def __init__(self) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "anthropic package required for ClaudeGenerator. "
                "Install with: pip install anthropic"
            ) from exc

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set — cannot initialise ClaudeGenerator."
            )

        import anthropic as _anthropic
        self._client   = _anthropic.Anthropic(api_key=api_key)
        self._fallback = TemplateGenerator()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call(self, messages: List[dict], max_tokens: int = 200) -> Optional[str]:
        """
        Make one Claude API call. Returns the text or None on any failure.
        Callers must fall back to TemplateGenerator when None is returned.
        """
        try:
            resp = self._client.messages.create(
                model      = "claude-haiku-4-5-20251001",
                max_tokens = max_tokens,
                system     = self._SYSTEM,
                messages   = messages,
            )
            text = resp.content[0].text.strip()
            # Log token usage (NDA: no content logged)
            usage = getattr(resp, "usage", None)
            if usage:
                print(
                    f"[ClaudeGenerator] tokens in={usage.input_tokens} "
                    f"out={usage.output_tokens}"
                )
            return text or None
        except Exception as e:
            print(f"[ClaudeGenerator] API error (falling back to template): {e}")
            return None

    def _recent_turns(self, session: V2Session, limit: int = 8) -> List[dict]:
        """
        Convert the last `limit` session turns to Anthropic message format.
        Skips system-injected [INTERNAL] messages.
        """
        msgs = []
        for turn in session.turns[-limit:]:
            if "[INTERNAL]" in turn.text:
                continue
            role = "assistant" if turn.role == "assistant" else "user"
            msgs.append({"role": role, "content": turn.text})
        return msgs

    # ------------------------------------------------------------------
    # TurnGenerator interface
    # ------------------------------------------------------------------

    def opening(self, session: V2Session) -> str:
        """Template is perfectly adequate for the opening line."""
        return self._fallback.opening(session)

    def ask(self, session: V2Session, question: QuestionBankItem) -> str:
        """
        Template is used for the first question ask.
        In Mode B follow-up, probe_overrides always supplies the Phase 1 probe text
        so _generator.ask() is rarely called — template is fine here.
        """
        return self._fallback.ask(session, question)

    def clarify(
        self,
        session:         V2Session,
        question:        QuestionBankItem,
        clarify_attempt: int,
    ) -> str:
        """
        Generate a targeted follow-up when the user response was vague.
        Detects which signal categories (owner/KPI/cadence/system/example) are
        absent and tells Claude exactly what to probe for.
        Falls back to TemplateGenerator on any API failure.
        """
        from ..state_machine import missing_signals as _missing_signals

        turns = self._recent_turns(session, limit=6)
        if not turns:
            return self._fallback.clarify(session, question, clarify_attempt)

        # Identify the specific missing elements from the last user answer
        last_user_text = next(
            (t.text for t in reversed(session.turns) if t.role == "user"), ""
        )
        missing = _missing_signals(last_user_text) if last_user_text else []
        # Priority: ownership first, then metrics, cadence, system, specificity
        priority_order = ["ownership", "metrics", "cadence", "system", "specificity"]
        ordered_missing = [s for s in priority_order if s in missing]
        missing_str = (
            f"a named {ordered_missing[0]}" if ordered_missing else "concrete specifics"
        )
        all_missing_str = ", ".join(ordered_missing[:3]) or "concrete specifics"

        turns.append({
            "role": "user",
            "content": (
                f"[INTERNAL] Respondent answered about '{question.label}' but is missing: "
                f"{all_missing_str}. Clarification attempt {clarify_attempt + 1}. "
                f"Ask exactly one follow-up question focused on {missing_str}. "
                "Reference what they just said to make the question feel responsive. "
                "Return only the question text — no preamble, no explanation."
            ),
        })

        result = self._call(turns, max_tokens=120)
        return result or self._fallback.clarify(session, question, clarify_attempt)

    def probe(
        self,
        session:       V2Session,
        question:      QuestionBankItem,
        probe_context: Optional[str] = None,
    ) -> str:
        """Delegate to template — probe text is already McKinsey-quality."""
        return self._fallback.probe(session, question, probe_context)

    def wrap(self, session: V2Session) -> str:
        """
        Generate a brief, personalized closing that references what was discussed.
        Falls back to TemplateGenerator on API failure.
        """
        name  = session.respondent_name or "you"
        turns = self._recent_turns(session, limit=10)
        if not turns:
            return self._fallback.wrap(session)

        n_answered = len(session.extracted_answers)
        turns.append({
            "role": "user",
            "content": (
                f"[INTERNAL] The follow-up interview for {name} is complete. "
                f"{n_answered} topic(s) were addressed. "
                "Write a 2-sentence closing statement that: (1) thanks them briefly, "
                "(2) notes that their responses will inform the updated maturity assessment. "
                "Be specific about what was covered if possible. "
                "Return only the closing text — no preamble."
            ),
        })

        result = self._call(turns, max_tokens=120)
        return result or self._fallback.wrap(session)
