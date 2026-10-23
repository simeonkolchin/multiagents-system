from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def create(
    session: AsyncSession, email: str, password_hash: str, name: str
) -> User:
    user = User(email=email, password_hash=password_hash, name=name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
