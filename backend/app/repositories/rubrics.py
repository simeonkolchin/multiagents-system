from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Rubric


async def create(
    session: AsyncSession,
    role: str,
    level: str,
    competencies: list[dict[str, Any]],
    owner_id: int | None = None,
) -> Rubric:
    rubric = Rubric(
        role=role, level=level, competencies=competencies, owner_id=owner_id
    )
    session.add(rubric)
    await session.commit()
    await session.refresh(rubric)
    return rubric


async def get(session: AsyncSession, rubric_id: int) -> Rubric | None:
    return await session.get(Rubric, rubric_id)


async def list_all(
    session: AsyncSession, owner_id: int | None = None
) -> list[Rubric]:
    query = select(Rubric).order_by(Rubric.id)
    if owner_id is not None:
        query = query.where(Rubric.owner_id == owner_id)
    result = await session.execute(query)
    return list(result.scalars().all())
