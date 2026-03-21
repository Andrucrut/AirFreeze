from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDRepository
from app.models.search_history import SearchHistory


class SearchHistoryCRUD(CRUDRepository[SearchHistory]):
    def __init__(self) -> None:
        super().__init__(SearchHistory)

    async def create_entry(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        from_city: str,
        to_city: str,
        flight_date: date,
        passengers: int,
        sort_by: str,
        sort_order: str,
        max_price: float | None,
        max_stops: int | None,
        result_count: int,
    ) -> SearchHistory:
        row = SearchHistory(
            user_id=user_id,
            from_city=from_city.strip(),
            to_city=to_city.strip(),
            flight_date=flight_date,
            passengers=passengers,
            sort_by=sort_by,
            sort_order=sort_order,
            max_price=max_price,
            max_stops=max_stops,
            result_count=result_count,
            created_at=datetime.now(timezone.utc),
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
        return row

    async def list_for_user(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        skip: int,
        limit: int,
    ) -> tuple[list[SearchHistory], int]:
        count_q = select(func.count()).select_from(SearchHistory).where(SearchHistory.user_id == user_id)
        total = int((await session.execute(count_q)).scalar_one())
        q = (
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = list((await session.execute(q)).scalars().all())
        return rows, total

    async def delete_for_user(self, session: AsyncSession, *, user_id: int, entry_id: int) -> bool:
        row = await self.get_by_id(session, entry_id)
        if row is None or row.user_id != user_id:
            return False
        await session.delete(row)
        await session.flush()
        return True


search_history_crud = SearchHistoryCRUD()
