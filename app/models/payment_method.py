from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentMethod(Base):
    """Сохранённая карта: только маска и имя держателя (PAN и CVC не хранятся)."""

    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False, default="Карта")
    last_four: Mapped[str] = mapped_column(String(4), nullable=False)
    holder_name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="payment_methods")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="payment_method")
