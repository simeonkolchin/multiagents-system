from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.repositories import interviews as repo
from app.schemas.interview import Episode, InterviewCreate, InterviewRead
from app.services.transcript import parse_transcript

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _to_read(record) -> InterviewRead:
    return InterviewRead(
        id=record.id,
        title=record.title,
        episodes=[Episode(**e) for e in record.episodes],
    )


@router.post("", response_model=InterviewRead)
async def create_interview(
    payload: InterviewCreate, session: SessionDep, user: CurrentUser
) -> InterviewRead:
    episodes = parse_transcript(payload.raw_text)
    if not episodes:
        raise HTTPException(status_code=422, detail="не удалось разобрать расшифровку")
    record = await repo.create(
        session,
        title=payload.title,
        raw_text=payload.raw_text,
        episodes=[e.model_dump() for e in episodes],
        owner_id=user.id,
    )
    return _to_read(record)


@router.get("", response_model=list[InterviewRead])
async def list_interviews(session: SessionDep, user: CurrentUser) -> list[InterviewRead]:
    return [_to_read(r) for r in await repo.list_all(session, owner_id=user.id)]


@router.get("/{interview_id}", response_model=InterviewRead)
async def get_interview(
    interview_id: int, session: SessionDep, user: CurrentUser
) -> InterviewRead:
    record = await repo.get(session, interview_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="interview not found")
    return _to_read(record)
