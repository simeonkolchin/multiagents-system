from app.agents import prompts
from app.agents.base import Agent
from app.config import Settings
from app.llm.client import LLMClient
from app.schemas.evaluation import ApproachMetrics, EvaluationResult
from app.schemas.interview import Episode
from app.schemas.rubric import Competency
from app.schemas.scorecard import Scorecard
from app.services import heuristics


def compute_metrics(
    approach: str,
    scorecard: Scorecard,
    episodes: list[Episode],
    competencies: list[Competency],
) -> ApproachMetrics:
    hinted = heuristics.hinted_competency_ids(episodes, competencies)
    told_only = heuristics.told_only_competency_ids(episodes, competencies)
    no_data = heuristics.no_data_competency_ids(episodes, competencies)
    candidate_ids = {
        c.id: set(heuristics.match_competency(episodes, c).candidate_ids)
        for c in competencies
    }

    unsupported = 0
    preserved = 0
    for row in scorecard.rows:
        cid = row.competency_id
        refs = set(row.episode_refs)

        if cid in no_data and row.sufficiency != "no_data":
            unsupported += 1
        if cid in hinted and row.sufficiency == "confirmed" and row.provenance != "hinted":
            unsupported += 1
        if (
            cid in told_only
            and row.sufficiency == "confirmed"
            and row.evidence_kind not in ("told", "mixed")
        ):
            unsupported += 1
        if (
            row.sufficiency == "confirmed"
            and refs
            and not (refs & candidate_ids.get(cid, set()))
        ):
            unsupported += 1

        if cid in hinted and row.provenance == "hinted":
            preserved += 1
        if cid in told_only and row.evidence_kind in ("told", "mixed"):
            preserved += 1
        if cid in no_data and row.sufficiency == "no_data":
            preserved += 1

    return ApproachMetrics(
        approach=approach,
        unsupported_conclusions=unsupported,
        preserved_caveats=preserved,
        estimated_human_edits=unsupported,
        rows=len(scorecard.rows),
        flagged_disputes=len(scorecard.disputes),
    )


class Evaluator:
    def __init__(self, client: LLMClient, settings: Settings) -> None:
        self._baseline = Agent(client, settings, prompts.BASELINE, use_tools=False)

    async def baseline_scorecard(
        self,
        role: str,
        level: str,
        competencies: list[Competency],
        episodes: list[Episode],
        resume: str = "",
    ) -> Scorecard:
        payload = {
            "task": "baseline_scorecard",
            "rubric": {
                "role": role,
                "level": level,
                "competencies": [c.model_dump() for c in competencies],
            },
            "episodes": [e.model_dump() for e in episodes],
            "resume": resume,
        }
        data = await self._baseline.run(payload)
        return Scorecard(**data)

    async def run(
        self,
        role: str,
        level: str,
        competencies: list[Competency],
        episodes: list[Episode],
        multi_agent_scorecard: Scorecard,
        resume: str = "",
    ) -> EvaluationResult:
        baseline = await self.baseline_scorecard(
            role, level, competencies, episodes, resume
        )
        ma_metrics = compute_metrics(
            "multi_agent", multi_agent_scorecard, episodes, competencies
        )
        base_metrics = compute_metrics("baseline", baseline, episodes, competencies)
        summary = (
            f"Мультиагентная система: {ma_metrics.unsupported_conclusions} "
            f"неподтверждённых выводов, {ma_metrics.preserved_caveats} сохранённых "
            f"оговорок, {ma_metrics.flagged_disputes} явно помеченных спорных. "
            f"Один LLM-вызов: {base_metrics.unsupported_conclusions} неподтверждённых "
            f"выводов, {base_metrics.preserved_caveats} оговорок."
        )
        return EvaluationResult(
            multi_agent=ma_metrics,
            baseline=base_metrics,
            multi_agent_scorecard=multi_agent_scorecard,
            baseline_scorecard=baseline,
            summary=summary,
        )
