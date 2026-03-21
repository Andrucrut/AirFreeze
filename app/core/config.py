from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _to_asyncpg_url(url: str) -> str:
    """Railway/Render/Vercel Postgres часто отдают postgres:// или postgresql:// без +asyncpg."""
    u = url.strip()
    if u.startswith("postgresql+asyncpg://"):
        return u
    if u.startswith("postgres://"):
        return "postgresql+asyncpg://" + u[len("postgres://") :]
    if u.startswith("postgresql://"):
        return "postgresql+asyncpg://" + u[len("postgresql://") :]
    return u


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AirFreeze"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://airfreeze:airfreeze@localhost:5433/airfreeze"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: object) -> object:
        if isinstance(v, str):
            return _to_asyncpg_url(v)
        return v

    # Через запятую; переменная окружения CORS_ORIGINS (см. .env.example)
    cors_origins: str = ""

    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    freeze_ttl_hours: int = 24

    # If set, the first newly created account with this email becomes admin (one-time bootstrap).
    bootstrap_admin_email: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def cors_allow_origins() -> list[str]:
    raw = settings.cors_origins.strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]
