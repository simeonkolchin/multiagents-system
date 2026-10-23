from app.schemas.interview import Episode, Speaker
from app.transcribe.client import TranscriptResult, TranscriptSegment


def seconds_to_tc(value: float) -> str:
    total = int(round(value))
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def tc_to_seconds(value: str) -> float:
    parts = [int(p) for p in value.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    hours, minutes, seconds = parts
    return hours * 3600 + minutes * 60 + seconds


def _assign_roles(segments: list[TranscriptSegment]) -> dict[int, Speaker]:
    speakers = {s.speaker for s in segments if s.speaker is not None}
    if len(speakers) < 2:
        return {}
    question_ratio: dict[int, float] = {}
    for speaker in speakers:
        owned = [s for s in segments if s.speaker == speaker]
        questions = sum(1 for s in owned if "?" in s.text)
        question_ratio[speaker] = questions / max(len(owned), 1)
    interviewer = max(question_ratio, key=question_ratio.get)
    return {
        speaker: ("interviewer" if speaker == interviewer else "candidate")
        for speaker in speakers
    }


def result_to_episodes(result: TranscriptResult) -> list[Episode]:
    roles = _assign_roles(result.segments)
    episodes: list[Episode] = []
    for index, segment in enumerate(result.segments, start=1):
        speaker: Speaker = "unknown"
        if segment.speaker is not None:
            speaker = roles.get(segment.speaker, "unknown")
        episodes.append(
            Episode(
                id=index,
                t=seconds_to_tc(segment.start),
                speaker=speaker,
                text=segment.text.strip(),
            )
        )
    return episodes
