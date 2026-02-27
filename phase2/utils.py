"""
phase2/utils.py — Shared utilities for Phase 2.
"""

from __future__ import annotations

import os
from typing import Literal

from .generation.base import TurnGenerator
from .generation.template_generator import TemplateGenerator

GenerationMode = Literal["template", "claude", "hybrid"]


def get_generation_mode() -> GenerationMode:
    """
    Read GENERATION_MODE env var. Falls back to "template" if unset or invalid.
    Valid values: template | claude | hybrid
    """
    mode = os.getenv("GENERATION_MODE", "template").lower().strip()
    if mode in ("claude", "hybrid"):
        return mode  # type: ignore[return-value]
    return "template"


def build_generator() -> TurnGenerator:
    """
    Factory: return the appropriate TurnGenerator based on GENERATION_MODE.

    - template (default): TemplateGenerator — deterministic, no LLM required.
    - claude:             ClaudeGenerator   — requires ANTHROPIC_API_KEY (Chunk 3).
    - hybrid:             Tries Claude, falls back to TemplateGenerator on any failure.
    """
    mode = get_generation_mode()

    if mode in ("claude", "hybrid"):
        try:
            from .generation.claude_generator import ClaudeGenerator
            return ClaudeGenerator()
        except (ImportError, NotImplementedError, Exception):
            if mode == "claude":
                raise  # In pure claude mode, don't silently fall back
            # hybrid mode: fall through to template

    return TemplateGenerator()
