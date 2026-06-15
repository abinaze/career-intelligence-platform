"""
SQLAlchemy async engine and session factory.

Uses async engine with connection pooling for production performance.
All database access should go through get_db() dependency.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.config.settings import get_settings
from src.core.logging.setup import get_logger

logger = get_logger(__name__)
_settings = get_settings()


def create_engine(database_url: str | None = None) -> Any:
    """
    Create the async SQLAlchemy engine.
    Uses NullPool in testing to prevent connection leaks.
    """
    url = database_url or _settings.DATABASE_URL

    engine_kwargs: dict[str, Any] = {
        "echo": _settings.DATABASE_ECHO,
        "future": True,
    }

    if _settings.ENVIRONMENT == "testing":
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_size"] = _settings.DATABASE_POOL_SIZE
        engine_kwargs["max_overflow"] = _settings.DATABASE_MAX_OVERFLOW
        engine_kwargs["pool_timeout"] = _settings.DATABASE_POOL_TIMEOUT
        engine_kwargs["pool_pre_ping"] = True

    return create_async_engine(url, **engine_kwargs)


engine = create_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    Automatically commits on success and rolls back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Health check: verify database connectivity."""
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text

            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database connection check failed", error=str(e))
        return False
