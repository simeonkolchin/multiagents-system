from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AnalysisSession, EditLog


async def create(
    session: AsyncSession,
    rubric_id: int,
    interview_id: int,
    resume: str = "",
    owner_id: int | None = None,
) -> AnalysisSession:
    record = AnalysisSession(
        rubric_id=rubric_id,
        interview_id=interview_id,
        resume=resume,
        status="pending",
        owner_id=owner_id,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get(session: AsyncSession, session_id: int) -> AnalysisSession | None:
    return await session.get(AnalysisSession, session_id)


async def list_all(
    session: AsyncSession, owner_id: int | None = None
) -> list[AnalysisSession]:
    query = select(AnalysisSession).order_by(AnalysisSession.id.desc())
    if owner_id is not None:
        query = query.where(AnalysisSession.owner_id == owner_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def save_result(
    session: AsyncSession,
    record: AnalysisSession,
    scorecard: dict[str, Any],
    trace: dict[str, Any],
    status: str = "ready",
) -> AnalysisSession:
    record.scorecard = scorecard
    record.trace = trace
    record.status = status
    await session.commit()
    await session.refresh(record)
    return record


async def update_scorecard(
    session: AsyncSession, record: AnalysisSession, scorecard: dict[str, Any]
) -> AnalysisSession:
    record.scorecard = scorecard
    await session.commit()
    await session.refresh(record)
    return record


async def add_edit(
    session: AsyncSession,
    session_id: int,
    competency_id: str,
    action: str,
    payload: dict[str, Any],
) -> EditLog:
    edit = EditLog(
        session_id=session_id,
        competency_id=competency_id,
        action=action,
        payload=payload,
    )
    session.add(edit)
    await session.commit()
    await session.refresh(edit)
    return edit
