import re

from app.schemas.interview import Episode, Speaker

_LINE = re.compile(r"^\s*\[(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\]\s*(?P<rest>.*)$")

_INTERVIEWER = {"интервьюер", "interviewer", "и", "i"}
_CANDIDATE = {"кандидат", "candidate", "к", "c"}


def _speaker(label: str) -> Speaker:
    key = label.strip().lower()
    if key in _INTERVIEWER:
        return "interviewer"
    if key in _CANDIDATE:
        return "candidate"
    return "unknown"


def parse_transcript(raw_text: str) -> list[Episode]:
    episodes: list[Episode] = []
    next_id = 1
    for line in raw_text.splitlines():
        match = _LINE.match(line)
        if not match:
            if episodes and line.strip():
                episodes[-1].text = f"{episodes[-1].text} {line.strip()}".strip()
            continue
        rest = match.group("rest")
        speaker: Speaker = "unknown"
        text = rest
        if ":" in rest:
            label, _, body = rest.partition(":")
            if len(label) <= 24:
                speaker = _speaker(label)
                text = body.strip()
        episodes.append(
            Episode(id=next_id, t=match.group("time"), speaker=speaker, text=text.strip())
        )
        next_id += 1
    return episodes


def format_episodes(episodes: list[Episode]) -> str:
    labels = {"interviewer": "Интервьюер", "candidate": "Кандидат", "unknown": "Спикер"}
    lines = [f"[{ep.t}] {labels[ep.speaker]}: {ep.text}" for ep in episodes]
    return "\n".join(lines)
