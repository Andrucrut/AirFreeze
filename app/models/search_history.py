from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    from_city: Mapped[str] = mapped_column(String(128), nullable=False)
    to_city: Mapped[str] = mapped_column(String(128), nullable=False)
    flight_date: Mapped[date] = mapped_column(Date, nullable=False)
    passengers: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_by: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[str] = mapped_column(String(4), nullable=False)
    max_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_stops: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="search_history")
