from datetime import datetime

from app.schemas.base import SchemaBase


class FreezeCreateIn(SchemaBase):
    flight_id: int


class FreezeOut(SchemaBase):
    id: int
    user_id: int
    flight_id: int
    frozen_price: float
    freeze_fee_paid: float
    expires_at: datetime


class FreezeListOut(SchemaBase):
    items: list[FreezeOut]
    total: int
    skip: int
    limit: int
