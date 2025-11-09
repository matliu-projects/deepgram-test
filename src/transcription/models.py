from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class TranscriptSegment:
    """Represents a portion of a transcript with optional metadata."""

    text: str
    start: Optional[float] = None
    end: Optional[float] = None
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    """A normalized representation of a Deepgram transcription result."""

    text: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def speakers(self) -> Set[str]:
        """Return a set of speaker labels contained in the transcript."""

        return {segment.speaker for segment in self.segments if segment.speaker}


__all__ = ["TranscriptSegment", "TranscriptionResult"]
