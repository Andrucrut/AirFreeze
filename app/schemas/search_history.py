from datetime import date, datetime

from app.schemas.base import SchemaBase


class SearchHistoryOut(SchemaBase):
    id: int
    user_id: int
    from_city: str
    to_city: str
    flight_date: date
    passengers: int
    sort_by: str
    sort_order: str
    max_price: float | None
    max_stops: int | None
    result_count: int
    created_at: datetime


class SearchHistoryListOut(SchemaBase):
    items: list[SearchHistoryOut]
    total: int
    skip: int
    limit: int
