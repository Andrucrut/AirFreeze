from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDRepository
from app.models.user import User


class UserCRUD(CRUDRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    async def create(
        self,
        session: AsyncSession,
        *,
        email: str,
        password_hash: str,
        is_admin: bool = False,
    ) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            created_at=datetime.now(timezone.utc),
            is_admin=is_admin,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalar_one_or_none()

    async def list_paginated(self, session: AsyncSession, *, skip: int, limit: int) -> tuple[list[User], int]:
        count_result = await session.execute(select(func.count()).select_from(User))
        total = int(count_result.scalar_one())
        result = await session.execute(
            select(User).order_by(User.id.asc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def set_admin(self, session: AsyncSession, user: User, *, is_admin: bool) -> User:
        user.is_admin = is_admin
        await session.flush()
        await session.refresh(user)
        return user

    async def set_password_hash(self, session: AsyncSession, user: User, *, password_hash: str) -> User:
        user.password_hash = password_hash
        await session.flush()
        await session.refresh(user)
        return user


user_crud = UserCRUD()
