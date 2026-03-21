"""
CRUD layer base.

`CRUDRepository` is a thin generic wrapper around a SQLAlchemy model class.
Concrete repositories subclass or compose this for type-safe `get_by_id` etc.
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDRepository(Generic[ModelT]):
    """Generic async repository bound to one ORM model."""

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    async def get_by_id(self, session: AsyncSession, obj_id: int) -> ModelT | None:
        return await session.get(self.model, obj_id)

    async def get_by_field(self, session: AsyncSession, field_name: str, value: Any) -> ModelT | None:
        col = getattr(self.model, field_name)
        result = await session.execute(select(self.model).where(col == value))
        return result.scalar_one_or_none()
