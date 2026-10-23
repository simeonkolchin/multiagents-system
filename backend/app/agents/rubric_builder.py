from app.agents import prompts
from app.agents.base import Agent
from app.config import Settings
from app.llm.client import LLMClient
from app.schemas.rubric import Competency, RubricDraft


class RubricBuilder:
    def __init__(self, client: LLMClient, settings: Settings) -> None:
        self._agent = Agent(client, settings, prompts.RUBRIC_BUILDER, use_tools=False)

    async def run(self, vacancy: str) -> RubricDraft:
        payload = {"task": "build_rubric", "vacancy": vacancy}
        data = await self._agent.run(payload)
        competencies = [Competency(**c) for c in data.get("competencies", [])]
        return RubricDraft(
            role=data.get("role", ""),
            level=data.get("level", ""),
            competencies=competencies,
        )
