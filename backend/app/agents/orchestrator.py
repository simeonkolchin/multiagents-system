import asyncio
import logging
from typing import Any

from app.agents.competency_analyst import CompetencyAnalyst
from app.agents.evidence_reviewer import EvidenceReviewer
from app.agents.interview_analyst import InterviewAnalyst
from app.config import Settings
from app.llm.client import LLMClient
from app.llm.tools import ToolContext
from app.schemas.interview import Episode
from app.schemas.rubric import Competency
from app.schemas.scorecard import (
    CompetencyFinding,
    InterviewAnalysis,
    ReviewResult,
    Scorecard,
)
from app.services.review import deterministic_review, merge_reviews
from app.services.scorecard import synthesize_scorecard

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, client: LLMClient, settings: Settings) -> None:
        self._settings = settings
        self._competency_analyst = CompetencyAnalyst(client, settings)
        self._interview_analyst = InterviewAnalyst(client, settings)
        self._reviewer = EvidenceReviewer(client, settings)

    async def run(
        self,
        role: str,
        level: str,
        competencies: list[Competency],
        episodes: list[Episode],
        resume: str = "",
    ) -> tuple[Scorecard, dict[str, Any]]:
        rubric = {
            "role": role,
            "level": level,
            "competencies": [c.model_dump() for c in competencies],
        }
        context = ToolContext(episodes, competencies)

        findings, interview_analysis = await asyncio.gather(
            self._safe_findings(rubric, episodes, context, resume, competencies),
            self._safe_analysis(rubric, episodes, context, resume),
        )
        findings_by_id = {f.competency_id: f for f in findings}

        review = merge_reviews(
            await self._safe_review(
                rubric, episodes, findings, interview_analysis, context, resume
            ),
            deterministic_review(episodes, competencies, findings),
        )

        iterations = 0
        review_history = [review.model_dump()]
        while review.reanalyze and iterations < self._settings.max_review_iterations:
            iterations += 1
            targets = [c for c in competencies if c.id in set(review.reanalyze)]
            if not targets:
                break
            subset_rubric = {**rubric, "competencies": [c.model_dump() for c in targets]}
            refreshed = await self._safe_findings(
                subset_rubric, episodes, context, resume, targets
            )
            for finding in refreshed:
                findings_by_id[finding.competency_id] = finding
            findings = list(findings_by_id.values())
            review = merge_reviews(
                await self._safe_review(
                    rubric, episodes, findings, interview_analysis, context, resume
                ),
                deterministic_review(episodes, competencies, findings),
            )
            review_history.append(review.model_dump())

        scorecard = synthesize_scorecard(
            role, level, competencies, episodes, findings, interview_analysis, review
        )
        trace = {
            "review_iterations": iterations,
            "unresolved_reanalyze": review.reanalyze,
            "reviews": review_history,
            "interview_analysis": interview_analysis.model_dump(),
        }
        return scorecard, trace

    async def _safe_findings(
        self,
        rubric: dict[str, Any],
        episodes: list[Episode],
        context: ToolContext,
        resume: str,
        competencies: list[Competency],
    ) -> list[CompetencyFinding]:
        try:
            return await self._competency_analyst.run(
                rubric, episodes, context, resume
            )
        except Exception:
            logger.exception("competency analyst failed")
            return self.empty_findings(competencies)

    async def _safe_analysis(
        self,
        rubric: dict[str, Any],
        episodes: list[Episode],
        context: ToolContext,
        resume: str,
    ) -> InterviewAnalysis:
        try:
            return await self._interview_analyst.run(rubric, episodes, context, resume)
        except Exception:
            logger.exception("interview analyst failed")
            return InterviewAnalysis()

    async def _safe_review(
        self,
        rubric: dict[str, Any],
        episodes: list[Episode],
        findings: list[CompetencyFinding],
        interview_analysis: InterviewAnalysis,
        context: ToolContext,
        resume: str,
    ) -> ReviewResult:
        try:
            return await self._reviewer.run(
                rubric, episodes, findings, interview_analysis, context, resume
            )
        except Exception:
            logger.exception("evidence reviewer failed")
            return ReviewResult()

    @staticmethod
    def empty_findings(competencies: list[Competency]) -> list[CompetencyFinding]:
        return [CompetencyFinding(competency_id=c.id) for c in competencies]
