from datetime import datetime
from typing import Literal, Self

from pydantic import Field, model_validator

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
    paid_at: datetime | None = None
    payment_method_id: int | None = None


class BookingPayIn(SchemaBase):
    """Оплата сохранённой картой или новой (данные карты не хранятся целиком)."""

    payment_method_id: int | None = None
    card_number: str | None = Field(default=None, max_length=23)
    card_holder: str | None = Field(default=None, max_length=128)
    cvc: str | None = Field(default=None, max_length=4)

    @model_validator(mode="after")
    def exactly_one_payment_path(self) -> Self:
        has_saved = self.payment_method_id is not None
        has_any_new = bool(self.card_number or self.card_holder or self.cvc)
        if has_saved and has_any_new:
            raise ValueError("Use either payment_method_id or new card fields, not both")
        if has_saved:
            if self.payment_method_id is not None and self.payment_method_id < 1:
                raise ValueError("Invalid payment_method_id")
            return self
        if not (self.card_number and self.card_holder and self.cvc):
            raise ValueError("For a new card, provide card_number, card_holder, and cvc")
        return self


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
