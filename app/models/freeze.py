from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Freeze(Base):
    __tablename__ = "freezes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id", ondelete="CASCADE"), index=True)
    frozen_price: Mapped[float] = mapped_column(Float, nullable=False)
    freeze_fee_paid: Mapped[float] = mapped_column(Float, nullable=False, default=30.0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="freezes")
    flight: Mapped["Flight"] = relationship(back_populates="freezes")
