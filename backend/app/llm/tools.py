from typing import Any

from app.schemas.interview import Episode
from app.schemas.rubric import Competency

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_transcript",
            "description": (
                "Найти реплики в расшифровке по ключевым словам. "
                "Можно ограничить поиск ролью говорящего."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "speaker": {
                        "type": "string",
                        "enum": ["interviewer", "candidate", "any"],
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_episode_context",
            "description": "Открыть полный контекст эпизода и соседних реплик.",
            "parameters": {
                "type": "object",
                "properties": {
                    "episode_id": {"type": "integer"},
                    "window": {"type": "integer"},
                },
                "required": ["episode_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rubric",
            "description": "Получить утверждённую рубрику или одну компетенцию.",
            "parameters": {
                "type": "object",
                "properties": {"competency_id": {"type": "string"}},
            },
        },
    },
]


class ToolContext:
    def __init__(self, episodes: list[Episode], competencies: list[Competency]) -> None:
        self._episodes = episodes
        self._by_id = {ep.id: ep for ep in episodes}
        self._competencies = competencies

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "search_transcript":
            return self._search(
                str(arguments.get("query", "")),
                str(arguments.get("speaker", "any")),
            )
        if name == "get_episode_context":
            return self._context(
                int(arguments.get("episode_id", -1)),
                int(arguments.get("window", 2)),
            )
        if name == "get_rubric":
            return self._rubric(arguments.get("competency_id"))
        return {"error": f"unknown tool {name}"}

    def _search(self, query: str, speaker: str) -> dict[str, Any]:
        terms = [t.lower() for t in query.split() if t]
        matches = []
        for ep in self._episodes:
            if speaker in ("interviewer", "candidate") and ep.speaker != speaker:
                continue
            text = ep.text.lower()
            if any(term in text for term in terms) or not terms:
                matches.append(ep.model_dump())
        return {"matches": matches[:20]}

    def _context(self, episode_id: int, window: int) -> dict[str, Any]:
        if episode_id not in self._by_id:
            return {"error": "episode not found"}
        ids = sorted(self._by_id)
        idx = ids.index(episode_id)
        lo = max(0, idx - window)
        hi = min(len(ids), idx + window + 1)
        window_ids = ids[lo:hi]
        return {"episodes": [self._by_id[i].model_dump() for i in window_ids]}

    def _rubric(self, competency_id: str | None) -> dict[str, Any]:
        if competency_id:
            for comp in self._competencies:
                if comp.id == competency_id:
                    return comp.model_dump()
            return {"error": "competency not found"}
        return {"competencies": [c.model_dump() for c in self._competencies]}
