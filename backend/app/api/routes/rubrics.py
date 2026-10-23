from fastapi import APIRouter, HTTPException

from app.agents.rubric_builder import RubricBuilder
from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.llm.factory import build_llm_client
from app.repositories import rubrics as repo
from app.schemas.rubric import (
    GenerateRubricRequest,
    RubricCreate,
    RubricDraft,
    RubricRead,
)

router = APIRouter(prefix="/rubrics", tags=["rubrics"])


def _to_read(record) -> RubricRead:
    return RubricRead(
        id=record.id,
        role=record.role,
        level=record.level,
        competencies=record.competencies,
    )


@router.post("", response_model=RubricRead)
async def create_rubric(
    payload: RubricCreate, session: SessionDep, user: CurrentUser
) -> RubricRead:
    record = await repo.create(
        session,
        role=payload.role,
        level=payload.level,
        competencies=[c.model_dump() for c in payload.competencies],
        owner_id=user.id,
    )
    return _to_read(record)


@router.post("/generate", response_model=RubricDraft)
async def generate_rubric(
    payload: GenerateRubricRequest, settings: SettingsDep, user: CurrentUser
) -> RubricDraft:
    if not payload.vacancy.strip():
        raise HTTPException(status_code=422, detail="пустой текст вакансии")
    builder = RubricBuilder(build_llm_client(settings), settings)
    return await builder.run(payload.vacancy)


@router.get("", response_model=list[RubricRead])
async def list_rubrics(session: SessionDep, user: CurrentUser) -> list[RubricRead]:
    return [_to_read(r) for r in await repo.list_all(session, owner_id=user.id)]


@router.get("/{rubric_id}", response_model=RubricRead)
async def get_rubric(
    rubric_id: int, session: SessionDep, user: CurrentUser
) -> RubricRead:
    record = await repo.get(session, rubric_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="rubric not found")
    return _to_read(record)
