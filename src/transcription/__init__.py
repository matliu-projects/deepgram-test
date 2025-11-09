"""Transcription services and adapters."""

from __future__ import annotations

from .models import TranscriptSegment, TranscriptionResult

__all__ = ["Transcriber", "TranscriptSegment", "TranscriptionResult"]


class Transcriber:  # pragma: no cover - placeholder
    """Placeholder for transcription service logic."""

    def transcribe(self, audio: bytes) -> str:
        return ""
