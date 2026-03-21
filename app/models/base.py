"""
ORM model layer conventions.

All concrete models inherit from `app.db.base.Base` (DeclarativeBase).
Use `Mapped[]` and `mapped_column()` (SQLAlchemy 2.0 style) for columns.
"""

from app.db.base import Base as DeclarativeBase

__all__ = ("DeclarativeBase",)
