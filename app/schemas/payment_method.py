from datetime import datetime

from pydantic import Field

from app.schemas.base import SchemaBase


class PaymentMethodCreateIn(SchemaBase):
    """PAN и CVC не сохраняются; сохраняются только последние 4 цифры и имя держателя."""

    card_number: str = Field(min_length=13, max_length=23)
    card_holder: str = Field(min_length=2, max_length=128)
    cvc: str = Field(min_length=3, max_length=4)


class PaymentMethodOut(SchemaBase):
    id: int
    label: str
    last_four: str
    holder_name: str
    created_at: datetime
