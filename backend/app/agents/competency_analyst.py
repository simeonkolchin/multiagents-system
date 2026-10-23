from typing import Any

from app.agents import prompts
from app.agents.base import Agent
from app.config import Settings
from app.llm.client import LLMClient
from app.llm.tools import ToolContext
from app.schemas.interview import Episode
from app.schemas.scorecard import CompetencyFinding


class CompetencyAnalyst:
    def __init__(self, client: LLMClient, settings: Settings) -> None:
        self._agent = Agent(client, settings, prompts.COMPETENCY_ANALYST)

    async def run(
        self,
        rubric: dict[str, Any],
        episodes: list[Episode],
        context: ToolContext,
        resume: str = "",
    ) -> list[CompetencyFinding]:
        payload = {
            "task": "competency_analysis",
            "rubric": rubric,
            "episodes": [e.model_dump() for e in episodes],
            "resume": resume,
        }
        data = await self._agent.run(payload, context)
        return [CompetencyFinding(**item) for item in data.get("findings", [])]
