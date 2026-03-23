from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoint import admin, auth, booking, flights, freeze, payment_methods, searches, users
from app.core.config import cors_allow_origins, settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        swagger_ui_parameters={"persistAuthorization": True},
        servers=[{"url": settings.api_base_url}],
    )
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(users.router)
    app.include_router(flights.router)
    app.include_router(searches.router)
    app.include_router(freeze.router)
    app.include_router(booking.router)
    app.include_router(payment_methods.router)

    # Без этого браузер с localhost:3000 получает 405 на OPTIONS (preflight) и логин с фронта не работает
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()
