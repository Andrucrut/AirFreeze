"""
API layer base.

Routers live under `app.api.endpoint`. Use `APIRouter(tags=...)` per resource;
aggregate them in `app.main` with `include_router`.
"""

from fastapi import APIRouter

__all__ = ("APIRouter",)
