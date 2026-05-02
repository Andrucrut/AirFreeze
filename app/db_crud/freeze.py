from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db_crud.base import CRUDRepository
from app.models.freeze import Freeze


class FreezeCRUD(CRUDRepository[Freeze]):
    def __init__(self) -> None:
        super().__init__(Freeze)

    async def create_for_flight(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        flight_id: int,
        price_at_freeze: float,
    ) -> Freeze:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=settings.freeze_ttl_hours)
        row = Freeze(
            user_id=user_id,
            flight_id=flight_id,
            frozen_price=price_at_freeze,
            expires_at=expires,
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
        return row

    async def list_for_user(self, session: AsyncSession, user_id: int) -> list[Freeze]:
        result = await session.execute(
            select(Freeze).where(Freeze.user_id == user_id).order_by(Freeze.expires_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_for_user_flight(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        flight_id: int,
        at: datetime | None = None,
    ) -> Freeze | None:
        now = at or datetime.now(timezone.utc)
        result = await session.execute(
            select(Freeze).where(
                and_(
                    Freeze.user_id == user_id,
                    Freeze.flight_id == flight_id,
                    Freeze.expires_at > now,
                )
            ).order_by(Freeze.expires_at.desc())
        )
        return result.scalars().first()

    async def list_paginated(
        self,
        session: AsyncSession,
        *,
        skip: int,
        limit: int,
        user_id: int | None = None,
    ) -> tuple[list[Freeze], int]:
        q = select(Freeze)
        count_q = select(func.count()).select_from(Freeze)
        if user_id is not None:
            q = q.where(Freeze.user_id == user_id)
            count_q = count_q.where(Freeze.user_id == user_id)
        q = q.order_by(Freeze.expires_at.desc()).offset(skip).limit(limit)
        total = int((await session.execute(count_q)).scalar_one())
        rows = list((await session.execute(q)).scalars().all())
        return rows, total

    async def delete(self, session: AsyncSession, row: Freeze) -> None:
        await session.delete(row)
        await session.flush()


freeze_crud = FreezeCRUD()
