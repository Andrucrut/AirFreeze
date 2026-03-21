from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDRepository
from app.db_crud.freeze import freeze_crud
from app.models.booking import Booking
from app.models.flight import Flight


class BookingCRUD(CRUDRepository[Booking]):
    def __init__(self) -> None:
        super().__init__(Booking)

    async def create_for_flight(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        flight: Flight,
    ) -> tuple[Booking, float]:
        active = await freeze_crud.get_active_for_user_flight(
            session, user_id=user_id, flight_id=flight.id
        )
        price = float(active.frozen_price) if active else float(flight.price)
        booking = Booking(
            user_id=user_id,
            flight_id=flight.id,
            price_paid=price,
            status="confirmed",
            created_at=datetime.now(timezone.utc),
        )
        session.add(booking)
        await session.flush()
        await session.refresh(booking)
        return booking, price

    async def list_for_user(self, session: AsyncSession, user_id: int) -> list[Booking]:
        result = await session.execute(
            select(Booking).where(Booking.user_id == user_id).order_by(Booking.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_paginated(
        self,
        session: AsyncSession,
        *,
        skip: int,
        limit: int,
        user_id: int | None = None,
    ) -> tuple[list[Booking], int]:
        q = select(Booking)
        count_q = select(func.count()).select_from(Booking)
        if user_id is not None:
            q = q.where(Booking.user_id == user_id)
            count_q = count_q.where(Booking.user_id == user_id)
        q = q.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        total = int((await session.execute(count_q)).scalar_one())
        rows = list((await session.execute(q)).scalars().all())
        return rows, total

    async def set_status(self, session: AsyncSession, booking: Booking, *, status: str) -> Booking:
        booking.status = status
        await session.flush()
        await session.refresh(booking)
        return booking

    async def delete(self, session: AsyncSession, booking: Booking) -> None:
        await session.delete(booking)
        await session.flush()


booking_crud = BookingCRUD()
