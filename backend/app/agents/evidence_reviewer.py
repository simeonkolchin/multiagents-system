from typing import Any

from app.agents import prompts
from app.agents.base import Agent
from app.config import Settings
from app.llm.client import LLMClient
from app.llm.tools import ToolContext
from app.schemas.interview import Episode
from app.schemas.scorecard import (
    CompetencyFinding,
    InterviewAnalysis,
    ReviewResult,
)


class EvidenceReviewer:
    def __init__(self, client: LLMClient, settings: Settings) -> None:
        self._agent = Agent(client, settings, prompts.EVIDENCE_REVIEWER)

    async def run(
        self,
        rubric: dict[str, Any],
        episodes: list[Episode],
        competency_findings: list[CompetencyFinding],
        interview_analysis: InterviewAnalysis,
        context: ToolContext,
        resume: str = "",
    ) -> ReviewResult:
        payload = {
            "task": "evidence_review",
            "rubric": rubric,
            "episodes": [e.model_dump() for e in episodes],
            "competency_findings": [f.model_dump() for f in competency_findings],
            "interview_analysis": interview_analysis.model_dump(),
            "resume": resume,
        }
        data = await self._agent.run(payload, context)
        return ReviewResult(**data)
