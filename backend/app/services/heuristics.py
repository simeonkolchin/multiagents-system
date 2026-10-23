from dataclasses import dataclass, field

from app.schemas.interview import Episode
from app.schemas.rubric import Competency

HINT_MARKERS = [
    "подскажу",
    "подсказ",
    "наводящ",
    "намекну",
    "давайте я подскаж",
    "с подсказк",
]
TOLD_MARKERS = [
    "я запускал",
    "мы запускали",
    "у нас в проде",
    "я поднимал",
    "я настраивал",
    "на прошлой работе",
    "я отвечаю за",
    "я делал",
]
SHOWN_MARKERS = [
    "потому что",
    "сначала",
    "затем",
    "я бы",
    "можно оценить",
    "давайте посчитаем",
    "сравнивал",
]
OVERBROAD_MARKERS = [
    "слабый",
    "слабо",
    "сильный",
    "плохо",
    "отличный",
    "не тянет",
    "хорошо разбирается",
]


def _contains_any(text: str, needles: list[str]) -> bool:
    low = text.lower()
    return any(n in low for n in needles)


def _matches_competency(text: str, competency: Competency) -> bool:
    low = text.lower()
    needles = [competency.name.lower()] + [k.lower() for k in competency.keywords]
    return any(n and n in low for n in needles)


@dataclass
class CompetencyMatch:
    competency_id: str
    candidate_ids: list[int] = field(default_factory=list)
    interviewer_ids: list[int] = field(default_factory=list)

    @property
    def any_ids(self) -> list[int]:
        return sorted(set(self.candidate_ids) | set(self.interviewer_ids))


@dataclass
class HintEvent:
    hint_episode_id: int
    answer_episode_id: int
    competency_ids: list[int] = field(default_factory=list)


def match_competency(episodes: list[Episode], competency: Competency) -> CompetencyMatch:
    match = CompetencyMatch(competency_id=competency.id)
    for ep in episodes:
        if not _matches_competency(ep.text, competency):
            continue
        if ep.speaker == "candidate":
            match.candidate_ids.append(ep.id)
        elif ep.speaker == "interviewer":
            match.interviewer_ids.append(ep.id)
    return match


def detect_hints(
    episodes: list[Episode], competencies: list[Competency]
) -> list[HintEvent]:
    ordered = sorted(episodes, key=lambda e: e.id)
    events: list[HintEvent] = []
    for idx, ep in enumerate(ordered):
        if ep.speaker != "interviewer" or not _contains_any(ep.text, HINT_MARKERS):
            continue
        answer = next(
            (nxt for nxt in ordered[idx + 1 :] if nxt.speaker == "candidate"), None
        )
        if answer is None:
            continue
        comp_ids = [c.id for c in competencies if _matches_competency(answer.text, c)]
        events.append(
            HintEvent(
                hint_episode_id=ep.id,
                answer_episode_id=answer.id,
                competency_ids=comp_ids,
            )
        )
    return events


def hinted_competency_ids(
    episodes: list[Episode], competencies: list[Competency]
) -> set[str]:
    ids: set[str] = set()
    for event in detect_hints(episodes, competencies):
        ids.update(str(c) for c in event.competency_ids)
    return ids


def told_only_competency_ids(
    episodes: list[Episode], competencies: list[Competency]
) -> set[str]:
    told: set[str] = set()
    shown: set[str] = set()
    for ep in episodes:
        if ep.speaker != "candidate":
            continue
        comp_ids = [c.id for c in competencies if _matches_competency(ep.text, c)]
        if _contains_any(ep.text, TOLD_MARKERS):
            told.update(comp_ids)
        if _contains_any(ep.text, SHOWN_MARKERS):
            shown.update(comp_ids)
    return told - shown


def evidence_kind_for(episode_text: str) -> str:
    told = _contains_any(episode_text, TOLD_MARKERS)
    shown = _contains_any(episode_text, SHOWN_MARKERS)
    if told and shown:
        return "mixed"
    if told:
        return "told"
    if shown:
        return "demonstrated"
    return "none"


def no_data_competency_ids(
    episodes: list[Episode], competencies: list[Competency]
) -> set[str]:
    missing: set[str] = set()
    for comp in competencies:
        if not match_competency(episodes, comp).any_ids:
            missing.add(comp.id)
    return missing


def overbroad_claims(
    episodes: list[Episode], competencies: list[Competency]
) -> list[dict]:
    matches = {c.id: match_competency(episodes, c) for c in competencies}
    hinted = hinted_competency_ids(episodes, competencies)
    claims: list[dict] = []
    for ep in episodes:
        if ep.speaker != "interviewer" or not _contains_any(ep.text, OVERBROAD_MARKERS):
            continue
        for comp in competencies:
            if not _matches_competency(ep.text, comp):
                continue
            match = matches[comp.id]
            weak_support = len(match.candidate_ids) <= 1 or comp.id in hinted
            if weak_support:
                claims.append(
                    {
                        "competency_id": comp.id,
                        "episode_id": ep.id,
                        "claim": ep.text,
                    }
                )
    return claims
