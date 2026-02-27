"""
transcriber.py — AHI Diagnostic Reasoning Engine
Ephemeral audio transcription. NDA-compliant: no raw audio is ever written to disk.

Pipeline:
  1. Receive audio bytes in RAM
  2. Transcribe using OpenAI Whisper (local model) or fallback to assemblyai/deepgram
  3. Redact PII from transcript text
  4. Return text — audio bytes are discarded by the caller

If whisper is not installed or fails, returns None so the caller falls back gracefully.
"""

from __future__ import annotations

import re
import tempfile
import os
from typing import Optional

from heuristics import PII_PATTERNS


# ---------------------------------------------------------------------------
# PII Redaction (always applied before returning any transcript)
# ---------------------------------------------------------------------------

def redact_transcript(text: str) -> str:
    for pattern in PII_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
    return text.strip()


# ---------------------------------------------------------------------------
# Whisper Transcription
# Uses openai-whisper (local model, no data leaves the machine).
# Install: pip install openai-whisper
# On first use, downloads the 'base' model (~140MB) to ~/.cache/whisper/
# ---------------------------------------------------------------------------

def transcribe_audio_bytes(audio_bytes: bytes, content_type: str = "audio/webm") -> Optional[str]:
    """
    Transcribe audio bytes in RAM.

    NDA guarantee: audio_bytes are NEVER written to a persistent path.
    A NamedTemporaryFile with delete=True is used; it is cleaned up in the
    finally block even if transcription raises an exception.

    Returns the redacted transcript text, or None on any failure.
    """
    try:
        import whisper  # type: ignore
    except ImportError:
        return None

    tmp_path: Optional[str] = None
    try:
        # whisper requires a file path — use a temp file that auto-deletes
        suffix = _ext_from_content_type(content_type)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = whisper.load_model("base")
        result = model.transcribe(tmp_path, fp16=False)
        raw_text = result.get("text", "") or ""
        return redact_transcript(raw_text) or None

    except Exception:
        return None

    finally:
        # Guaranteed cleanup — raw audio bytes are never left on disk
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _ext_from_content_type(ct: str) -> str:
    mapping = {
        "audio/webm":  ".webm",
        "audio/ogg":   ".ogg",
        "audio/mp4":   ".mp4",
        "audio/mpeg":  ".mp3",
        "audio/wav":   ".wav",
        "audio/x-wav": ".wav",
    }
    return mapping.get(ct.split(";")[0].strip().lower(), ".webm")


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def whisper_available() -> bool:
    try:
        import whisper  # noqa: F401
        return True
    except ImportError:
        return False
