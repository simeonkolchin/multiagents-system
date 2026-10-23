from pathlib import Path

from app.services.transcript import parse_transcript
from app.transcribe.client import TranscriptResult, TranscriptSegment
from app.transcribe.formatter import tc_to_seconds

_DEMO = Path(__file__).resolve().parent.parent / "seed" / "interview_demo.txt"
_ROLE_INDEX = {"interviewer": 0, "candidate": 1, "unknown": None}


class MockTranscriber:
    async def transcribe(
        self, audio: bytes, filename: str, content_type: str
    ) -> TranscriptResult:
        raw = _DEMO.read_text(encoding="utf-8")
        episodes = parse_transcript(raw)
        segments = []
        for episode in episodes:
            start = tc_to_seconds(episode.t)
            segments.append(
                TranscriptSegment(
                    start=start,
                    end=start + 8.0,
                    text=episode.text,
                    speaker=_ROLE_INDEX.get(episode.speaker),
                )
            )
        return TranscriptResult(
            text=" ".join(e.text for e in episodes),
            language="ru",
            duration=segments[-1].end if segments else 0.0,
            segments=segments,
        )
