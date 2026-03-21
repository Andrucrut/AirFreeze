"""
SQLAlchemy declarative base.

`Base` holds metadata for all ORM tables. Alembic imports this and all models
so that `target_metadata = Base.metadata` is complete for autogenerate.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Root declarative base for AirFreeze ORM models."""
