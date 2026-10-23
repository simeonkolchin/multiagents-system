from app.agents.orchestrator import Orchestrator
from app.config import get_settings
from app.llm.mock import MockLLMClient
from app.services.evaluation import Evaluator


async def test_full_pipeline_planted_situations(competencies, episodes):
    settings = get_settings()
    orchestrator = Orchestrator(MockLLMClient(), settings)
    scorecard, trace = await orchestrator.run(
        "ML-инженер", "middle", competencies, episodes
    )
    rows = {r.competency_id: r for r in scorecard.rows}

    assert rows["operations"].sufficiency == "no_data"
    assert rows["solution_design"].provenance == "hinted"
    assert rows["solution_design"].sufficiency == "partial"
    assert rows["solution_design"].disputed is True
    assert rows["experience_review"].evidence_kind == "told"
    assert rows["quality_eval"].sufficiency == "confirmed"
    assert trace["review_iterations"] >= 0


async def test_evaluation_prefers_multi_agent(competencies, episodes):
    settings = get_settings()
    orchestrator = Orchestrator(MockLLMClient(), settings)
    scorecard, _ = await orchestrator.run(
        "ML-инженер", "middle", competencies, episodes
    )
    evaluator = Evaluator(MockLLMClient(), settings)
    result = await evaluator.run(
        "ML-инженер", "middle", competencies, episodes, scorecard
    )
    assert result.baseline.unsupported_conclusions > result.multi_agent.unsupported_conclusions
    assert result.multi_agent.preserved_caveats > result.baseline.preserved_caveats
