"""ASGI entrypoint for local runs: `uvicorn main:app --reload`."""

from app.main import app

__all__ = ("app",)
