from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_city: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    to_city: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stops: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_price_refresh_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    freezes: Mapped[list["Freeze"]] = relationship(back_populates="flight", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="flight", cascade="all, delete-orphan")
