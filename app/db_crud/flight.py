from datetime import date, datetime, time, timezone
from random import Random
from typing import Literal

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db_crud.base import CRUDRepository
from app.models.flight import Flight


class FlightCRUD(CRUDRepository[Flight]):
    def __init__(self) -> None:
        super().__init__(Flight)

    async def list_paginated(
        self,
        session: AsyncSession,
        *,
        skip: int,
        limit: int,
        from_city: str | None = None,
        to_city: str | None = None,
    ) -> tuple[list[Flight], int]:
        q = select(Flight)
        count_q = select(func.count()).select_from(Flight)
        if from_city:
            q = q.where(Flight.from_city.ilike(from_city.strip()))
            count_q = count_q.where(Flight.from_city.ilike(from_city.strip()))
        if to_city:
            q = q.where(Flight.to_city.ilike(to_city.strip()))
            count_q = count_q.where(Flight.to_city.ilike(to_city.strip()))
        q = q.order_by(Flight.departure_time.asc()).offset(skip).limit(limit)
        total = int((await session.execute(count_q)).scalar_one())
        rows = list((await session.execute(q)).scalars().all())
        await self.refresh_prices_if_needed(session, rows)
        return rows, total

    async def create(
        self,
        session: AsyncSession,
        *,
        from_city: str,
        to_city: str,
        departure_time: datetime,
        arrival_time: datetime,
        price: float,
        stops: int = 0,
    ) -> Flight:
        flight = Flight(
            from_city=from_city.strip(),
            to_city=to_city.strip(),
            departure_time=departure_time,
            arrival_time=arrival_time,
            price=price,
            stops=stops,
            last_price_refresh_at=datetime.now(timezone.utc),
        )
        session.add(flight)
        await session.flush()
        await session.refresh(flight)
        return flight

    async def update(
        self,
        session: AsyncSession,
        flight: Flight,
        *,
        from_city: str | None = None,
        to_city: str | None = None,
        departure_time: datetime | None = None,
        arrival_time: datetime | None = None,
        price: float | None = None,
        stops: int | None = None,
    ) -> Flight:
        if from_city is not None:
            flight.from_city = from_city.strip()
        if to_city is not None:
            flight.to_city = to_city.strip()
        if departure_time is not None:
            flight.departure_time = departure_time
        if arrival_time is not None:
            flight.arrival_time = arrival_time
        if price is not None:
            flight.price = price
        if stops is not None:
            flight.stops = stops
        # Manual admin update means this value is already "today's current" one.
        flight.last_price_refresh_at = datetime.now(timezone.utc)
        await session.flush()
        await session.refresh(flight)
        return flight

    async def delete(self, session: AsyncSession, flight: Flight) -> None:
        await session.delete(flight)
        await session.flush()

    async def search(
        self,
        session: AsyncSession,
        *,
        from_city: str,
        to_city: str,
        flight_date: date,
        passengers: int,  # reserved for future fare rules / inventory
        sort_by: Literal["price", "duration", "departure_time"] = "departure_time",
        sort_order: Literal["asc", "desc"] = "asc",
        max_price: float | None = None,
        max_stops: int | None = None,
    ) -> list[Flight]:
        _ = passengers
        start = datetime.combine(flight_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(flight_date, time.max, tzinfo=timezone.utc)
        conditions = [
            Flight.from_city.ilike(from_city.strip()),
            Flight.to_city.ilike(to_city.strip()),
            Flight.departure_time >= start,
            Flight.departure_time <= end,
        ]
        if max_price is not None:
            conditions.append(Flight.price <= max_price)
        if max_stops is not None:
            conditions.append(Flight.stops <= max_stops)

        duration_expr = Flight.arrival_time - Flight.departure_time
        order_col = {
            "price": Flight.price,
            "duration": duration_expr,
            "departure_time": Flight.departure_time,
        }[sort_by]
        order_fn = asc if sort_order == "asc" else desc

        stmt = select(Flight).where(and_(*conditions)).order_by(order_fn(order_col))
        result = await session.execute(stmt)
        rows = list(result.scalars().all())
        await self.refresh_prices_if_needed(session, rows)
        return rows

    async def get_by_id(self, session: AsyncSession, obj_id: int) -> Flight | None:  # type: ignore[override]
        flight = await super().get_by_id(session, obj_id)
        if flight is None:
            return None
        await self.refresh_prices_if_needed(session, [flight])
        return flight

    async def refresh_prices_if_needed(self, session: AsyncSession, flights: list[Flight]) -> None:
        now = datetime.now(timezone.utc)
        changed = False
        for flight in flights:
            if flight.departure_time <= now:
                continue
            if (
                flight.last_price_refresh_at is not None
                and flight.last_price_refresh_at.date() >= now.date()
            ):
                continue
            self._apply_daily_change(flight, now)
            changed = True
        if changed:
            await session.flush()

    @staticmethod
    def _apply_daily_change(flight: Flight, now: datetime) -> None:
        # Deterministic per (flight_id, day): one change per day for each flight.
        seed = (flight.id * 10_000_019) ^ now.date().toordinal()
        rng = Random(seed)
        delta = float(rng.randint(settings.daily_price_change_min_rub, settings.daily_price_change_max_rub))
        direction = -1.0 if rng.random() < 0.5 else 1.0
        flight.price = round(max(1.0, float(flight.price) + direction * delta), 2)
        flight.last_price_refresh_at = now


flight_crud = FlightCRUD()
