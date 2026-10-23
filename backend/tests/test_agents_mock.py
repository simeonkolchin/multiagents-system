from app.agents.competency_analyst import CompetencyAnalyst
from app.agents.evidence_reviewer import EvidenceReviewer
from app.agents.interview_analyst import InterviewAnalyst
from app.config import get_settings
from app.llm.mock import MockLLMClient
from app.llm.tools import ToolContext


def _rubric(competencies):
    return {
        "role": "ML-инженер",
        "level": "middle",
        "competencies": [c.model_dump() for c in competencies],
    }


async def test_competency_analyst_marks_no_data(competencies, episodes):
    settings = get_settings()
    analyst = CompetencyAnalyst(MockLLMClient(), settings)
    context = ToolContext(episodes, competencies)
    findings = await analyst.run(_rubric(competencies), episodes, context)
    by_id = {f.competency_id: f for f in findings}
    assert by_id["operations"].sufficiency == "no_data"
    assert by_id["quality_eval"].sufficiency == "confirmed"
    assert by_id["solution_design"].sufficiency == "partial"


async def test_interview_analyst_detects_hint_and_told(competencies, episodes):
    settings = get_settings()
    analyst = InterviewAnalyst(MockLLMClient(), settings)
    context = ToolContext(episodes, competencies)
    analysis = await analyst.run(_rubric(competencies), episodes, context)
    hinted = {h.competency_id for h in analysis.hints}
    assert "solution_design" in hinted
    told = {e.competency_id for e in analysis.evidence if e.kind == "told"}
    assert "experience_review" in told


async def test_reviewer_flags_overbroad(competencies, episodes):
    settings = get_settings()
    comp = CompetencyAnalyst(MockLLMClient(), settings)
    intv = InterviewAnalyst(MockLLMClient(), settings)
    reviewer = EvidenceReviewer(MockLLMClient(), settings)
    context = ToolContext(episodes, competencies)
    findings = await comp.run(_rubric(competencies), episodes, context)
    analysis = await intv.run(_rubric(competencies), episodes, context)
    review = await reviewer.run(
        _rubric(competencies), episodes, findings, analysis, context
    )
    kinds = {(i.competency_id, i.kind) for i in review.issues}
    assert ("solution_design", "overbroad_conclusion") in kinds
