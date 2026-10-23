from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: int | None = None


@dataclass
class TranscriptResult:
    text: str
    language: str = ""
    duration: float = 0.0
    segments: list[TranscriptSegment] = field(default_factory=list)


@runtime_checkable
class Transcriber(Protocol):
    async def transcribe(
        self, audio: bytes, filename: str, content_type: str
    ) -> TranscriptResult: ...
