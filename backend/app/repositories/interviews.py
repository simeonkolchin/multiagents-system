from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Interview


async def create(
    session: AsyncSession,
    title: str,
    raw_text: str,
    episodes: list[dict[str, Any]],
    owner_id: int | None = None,
) -> Interview:
    interview = Interview(
        title=title, raw_text=raw_text, episodes=episodes, owner_id=owner_id
    )
    session.add(interview)
    await session.commit()
    await session.refresh(interview)
    return interview


async def get(session: AsyncSession, interview_id: int) -> Interview | None:
    return await session.get(Interview, interview_id)


async def list_all(
    session: AsyncSession, owner_id: int | None = None
) -> list[Interview]:
    query = select(Interview).order_by(Interview.id)
    if owner_id is not None:
        query = query.where(Interview.owner_id == owner_id)
    result = await session.execute(query)
    return list(result.scalars().all())
