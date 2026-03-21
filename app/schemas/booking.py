from datetime import datetime
from typing import Literal

from app.schemas.base import SchemaBase


class BookingCreateIn(SchemaBase):
    flight_id: int


class BookingOut(SchemaBase):
    id: int
    user_id: int
    flight_id: int
    price_paid: float
    status: str
    created_at: datetime


class BookingPatchIn(SchemaBase):
    status: Literal["confirmed", "cancelled"]


class BookingUserCancelIn(SchemaBase):
    """User may only cancel their own confirmed booking."""

    status: Literal["cancelled"] = "cancelled"


class BookingListOut(SchemaBase):
    items: list[BookingOut]
    total: int
    skip: int
    limit: int
