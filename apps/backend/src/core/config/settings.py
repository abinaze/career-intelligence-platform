"""
Application configuration via Pydantic Settings.

All environment variables are validated at startup.
Never access os.environ directly — always use the settings instance.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(v: Any) -> list[str]:
    """Parse CORS origins from comma-separated string or list."""
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",")]
    if isinstance(v, list):
        return v
    raise ValueError("CORS_ORIGINS must be a comma-separated string or list")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Career Intelligence Platform"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "AI-powered career guidance through behavioral analysis"
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # ── API ───────────────────────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: str | None = "/docs"
    REDOC_URL: str | None = "/redoc"
    OPENAPI_URL: str | None = "/openapi.json"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-USE-STRONG-SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors_origins)] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://cip_user:cip_password@localhost:5432/cip_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 20
    CACHE_TTL_SECONDS: int = 3600

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20

    # ── AI/ML ─────────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32
    FAISS_INDEX_PATH: str = "data/faiss/career_index.faiss"
    MODEL_CACHE_DIR: str = ".model_cache"

    # ── Chat / LLM ────────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str | None = None

    # ── Frontend (used to build BYOS OAuth redirect targets) ────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    # ── BYOS: Google Drive OAuth broker ──────────────────────────────────────
    # The backend never persists these tokens (see docs/architecture/byos.md).
    # It only brokers the OAuth handshake because the Google client *secret*
    # cannot live in browser JS; the resulting tokens are handed back to the
    # browser, which talks to the Drive REST API directly from then on.
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/storage/google-drive/callback"
    GOOGLE_DRIVE_SCOPES: list[str] = ["https://www.googleapis.com/auth/drive.appdata"]
    # Ticket: binds "a connect flow is underway" to a user_id across the
    # browser-navigation Google redirect (which carries no Authorization header).
    GOOGLE_DRIVE_TICKET_TTL_SECONDS: int = 300
    # Exchange code: stages freshly-issued tokens for a few seconds so they
    # never have to travel through a URL query string.
    GOOGLE_DRIVE_EXCHANGE_TTL_SECONDS: int = 60

    # ── Background Jobs ───────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Paths ─────────────────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parents[3]
    DATA_DIR: Path = BASE_DIR / "data"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def set_debug_from_environment(cls, v: Any, info: Any) -> bool:
        """Force DEBUG=False in production."""
        if info.data.get("ENVIRONMENT") == "production":
            return False
        return bool(v)

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"

    @property
    def docs_enabled(self) -> bool:
        return self.ENVIRONMENT not in ("production", "testing")


@lru_cache
def get_settings() -> Settings:
    """
    Return cached settings instance.
    Use get_settings() everywhere instead of constructing Settings() directly.
    """
    return Settings()


settings = get_settings()
