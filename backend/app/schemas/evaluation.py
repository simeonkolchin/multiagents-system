from pydantic import BaseModel, Field

from app.schemas.scorecard import Scorecard


class ApproachMetrics(BaseModel):
    approach: str
    unsupported_conclusions: int = 0
    preserved_caveats: int = 0
    estimated_human_edits: int = 0
    rows: int = 0
    flagged_disputes: int = 0


class EvaluationResult(BaseModel):
    multi_agent: ApproachMetrics
    baseline: ApproachMetrics
    multi_agent_scorecard: Scorecard = Field(default_factory=Scorecard)
    baseline_scorecard: Scorecard = Field(default_factory=Scorecard)
    summary: str = ""
