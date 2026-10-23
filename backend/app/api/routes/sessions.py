from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import Orchestrator
from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.db.models import AnalysisSession
from app.llm.factory import build_llm_client
from app.repositories import interviews as interviews_repo
from app.repositories import rubrics as rubrics_repo
from app.repositories import sessions as sessions_repo
from app.schemas.interview import Episode
from app.schemas.rubric import Competency
from app.schemas.scorecard import (
    DisputeRequest,
    EditConclusion,
    InterviewerClaimAudit,
    Scorecard,
)
from app.schemas.session import (
    AuditRequest,
    SessionCreate,
    SessionRead,
    SessionSummary,
)
from app.services.scorecard import apply_dispute, apply_edit, audit_interviewer_claim

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_read(record: AnalysisSession) -> SessionRead:
    return SessionRead(
        id=record.id,
        rubric_id=record.rubric_id,
        interview_id=record.interview_id,
        status=record.status,
        scorecard=Scorecard(**record.scorecard) if record.scorecard else Scorecard(),
        trace=record.trace or {},
    )


async def _load_context(
    session: SessionDep, record: AnalysisSession
) -> tuple[str, str, list[Competency], list[Episode]]:
    rubric = await rubrics_repo.get(session, record.rubric_id)
    interview = await interviews_repo.get(session, record.interview_id)
    if rubric is None or interview is None:
        raise HTTPException(status_code=404, detail="rubric or interview missing")
    competencies = [Competency(**c) for c in rubric.competencies]
    episodes = [Episode(**e) for e in interview.episodes]
    return rubric.role, rubric.level, competencies, episodes


@router.post("", response_model=SessionRead)
async def create_session(
    payload: SessionCreate,
    session: SessionDep,
    settings: SettingsDep,
    user: CurrentUser,
) -> SessionRead:
    rubric = await rubrics_repo.get(session, payload.rubric_id)
    interview = await interviews_repo.get(session, payload.interview_id)
    if (
        rubric is None
        or interview is None
        or rubric.owner_id != user.id
        or interview.owner_id != user.id
    ):
        raise HTTPException(status_code=404, detail="rubric or interview not found")

    competencies = [Competency(**c) for c in rubric.competencies]
    episodes = [Episode(**e) for e in interview.episodes]

    record = await sessions_repo.create(
        session, rubric.id, interview.id, payload.resume, owner_id=user.id
    )
    orchestrator = Orchestrator(build_llm_client(settings), settings)
    scorecard, trace = await orchestrator.run(
        rubric.role, rubric.level, competencies, episodes, payload.resume
    )
    record = await sessions_repo.save_result(
        session, record, scorecard.model_dump(), trace, status="ready"
    )
    return _to_read(record)


@router.get("", response_model=list[SessionSummary])
async def list_sessions(
    session: SessionDep, user: CurrentUser
) -> list[SessionSummary]:
    records = await sessions_repo.list_all(session, owner_id=user.id)
    rubrics = {r.id: r for r in await rubrics_repo.list_all(session, owner_id=user.id)}
    interviews = {
        i.id: i for i in await interviews_repo.list_all(session, owner_id=user.id)
    }
    summaries = []
    for record in records:
        rubric = rubrics.get(record.rubric_id)
        interview = interviews.get(record.interview_id)
        summaries.append(
            SessionSummary(
                id=record.id,
                rubric_id=record.rubric_id,
                interview_id=record.interview_id,
                status=record.status,
                role=rubric.role if rubric else "",
                level=rubric.level if rubric else "",
                title=interview.title if interview else "",
                competencies=len(rubric.competencies) if rubric else 0,
                created_at=record.created_at,
            )
        )
    return summaries


@router.get("/{session_id}", response_model=SessionRead)
async def get_session_route(
    session_id: int, session: SessionDep, user: CurrentUser
) -> SessionRead:
    record = await sessions_repo.get(session, session_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="session not found")
    return _to_read(record)


@router.post("/{session_id}/edit", response_model=SessionRead)
async def edit_conclusion(
    session_id: int, payload: EditConclusion, session: SessionDep, user: CurrentUser
) -> SessionRead:
    record = await sessions_repo.get(session, session_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="session not found")
    scorecard = apply_edit(dict(record.scorecard), payload.competency_id, payload.conclusion)
    record = await sessions_repo.update_scorecard(session, record, scorecard)
    await sessions_repo.add_edit(
        session, session_id, payload.competency_id, "edit", payload.model_dump()
    )
    return _to_read(record)


@router.post("/{session_id}/dispute", response_model=SessionRead)
async def dispute_conclusion(
    session_id: int, payload: DisputeRequest, session: SessionDep, user: CurrentUser
) -> SessionRead:
    record = await sessions_repo.get(session, session_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="session not found")
    scorecard = apply_dispute(dict(record.scorecard), payload.competency_id, payload.reason)
    record = await sessions_repo.update_scorecard(session, record, scorecard)
    await sessions_repo.add_edit(
        session, session_id, payload.competency_id, "dispute", payload.model_dump()
    )
    return _to_read(record)


@router.post("/{session_id}/audit", response_model=InterviewerClaimAudit)
async def audit_claim(
    session_id: int, payload: AuditRequest, session: SessionDep, user: CurrentUser
) -> InterviewerClaimAudit:
    record = await sessions_repo.get(session, session_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="session not found")
    _, _, competencies, episodes = await _load_context(session, record)
    return audit_interviewer_claim(
        payload.competency_id, payload.claim, competencies, episodes
    )
