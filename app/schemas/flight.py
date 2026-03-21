from datetime import datetime

from pydantic import Field, computed_field

from app.schemas.base import SchemaBase


class FlightOut(SchemaBase):
    id: int
    from_city: str
    to_city: str
    departure_time: datetime
    arrival_time: datetime
    price: float
    stops: int = 0

    @computed_field
    @property
    def duration_minutes(self) -> int:
        delta = self.arrival_time - self.departure_time
        return max(0, int(delta.total_seconds() // 60))


class FlightCreateIn(SchemaBase):
    from_city: str = Field(min_length=1, max_length=128)
    to_city: str = Field(min_length=1, max_length=128)
    departure_time: datetime
    arrival_time: datetime
    price: float = Field(gt=0)
    stops: int = Field(default=0, ge=0)


class FlightPatchIn(SchemaBase):
    from_city: str | None = Field(default=None, min_length=1, max_length=128)
    to_city: str | None = Field(default=None, min_length=1, max_length=128)
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    price: float | None = Field(default=None, gt=0)
    stops: int | None = Field(default=None, ge=0)


class FlightListOut(SchemaBase):
    items: list[FlightOut]
    total: int
    skip: int
    limit: int
