import json

from app.agents import prompts
from app.llm.client import LLMClient
from app.schemas.interview import Episode, Speaker

_VALID: set[Speaker] = {"interviewer", "candidate"}


def _needs_assignment(episodes: list[Episode]) -> bool:
    speakers = {e.speaker for e in episodes}
    return speakers <= {"unknown"} or len(speakers) < 2


async def assign_roles(client: LLMClient, episodes: list[Episode]) -> list[Episode]:
    if not episodes or not _needs_assignment(episodes):
        return episodes

    payload = {"lines": [{"id": e.id, "text": e.text} for e in episodes]}
    messages = [
        {"role": "system", "content": prompts.ROLE_ASSIGNMENT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    try:
        result = await client.chat(
            messages, response_format={"type": "json_object"}
        )
        data = json.loads(result.content)
        roles = data.get("roles", {})
    except (ValueError, json.JSONDecodeError, KeyError):
        return episodes

    for episode in episodes:
        role = roles.get(str(episode.id))
        if role in _VALID:
            episode.speaker = role
    return episodes
