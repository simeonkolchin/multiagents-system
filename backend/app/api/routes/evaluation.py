from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.db.models import AnalysisSession
from app.llm.factory import build_llm_client
from app.repositories import interviews as interviews_repo
from app.repositories import rubrics as rubrics_repo
from app.repositories import sessions as sessions_repo
from app.schemas.evaluation import EvaluationResult
from app.schemas.interview import Episode
from app.schemas.rubric import Competency
from app.schemas.scorecard import Scorecard
from app.services.evaluation import Evaluator

router = APIRouter(prefix="/sessions", tags=["evaluation"])


@router.get("/{session_id}/evaluation", response_model=EvaluationResult)
async def evaluate_session(
    session_id: int, session: SessionDep, settings: SettingsDep, user: CurrentUser
) -> EvaluationResult:
    record: AnalysisSession | None = await sessions_repo.get(session, session_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="session not found")
    if not record.scorecard:
        raise HTTPException(status_code=409, detail="session has no scorecard yet")

    rubric = await rubrics_repo.get(session, record.rubric_id)
    interview = await interviews_repo.get(session, record.interview_id)
    if rubric is None or interview is None:
        raise HTTPException(status_code=404, detail="rubric or interview missing")

    competencies = [Competency(**c) for c in rubric.competencies]
    episodes = [Episode(**e) for e in interview.episodes]

    evaluator = Evaluator(build_llm_client(settings), settings)
    return await evaluator.run(
        rubric.role,
        rubric.level,
        competencies,
        episodes,
        Scorecard(**record.scorecard),
        record.resume or "",
    )
