"""
Pytest configuration and shared fixtures.

Each test gets a truncated database to avoid unique constraint violations.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
import structlog
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.db.engine import get_db
from src.db.models.base import Base
from src.main import create_application

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://cip_user:cip_password@localhost:5432/cip_test",
)

# Passed through to asyncpg.connect(): fail fast and loud if Postgres is
# unreachable or a query hangs (e.g. a stuck lock from a prior crashed
# run), rather than blocking the whole test session with no upper bound.
# Added after a CI run hung for 4+ hours with no clear error — these
# engines previously had no timeout at all.
_ENGINE_CONNECT_ARGS = {"timeout": 10, "command_timeout": 10}


def pytest_configure(config: Any) -> None:
    """Configure structlog to use stdlib so logger.name works in tests."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )


@pytest_asyncio.fixture(scope="session")
async def setup_database():  # type: ignore[no-untyped-def]
    """Create all tables once per session, drop after."""
    engine = create_async_engine(
        TEST_DATABASE_URL, poolclass=NullPool, connect_args=_ENGINE_CONNECT_ARGS
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_database: None) -> AsyncGenerator[None, None]:
    """Truncate all tables before each test to ensure isolation."""
    engine = create_async_engine(
        TEST_DATABASE_URL, poolclass=NullPool, connect_args=_ENGINE_CONNECT_ARGS
    )
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE refresh_tokens, psychometric_scores, "
                "assessment_sessions, user_profiles, users RESTART IDENTITY CASCADE"
            )
        )
    await engine.dispose()
    yield


@pytest_asyncio.fixture
async def db_session(setup_database: None) -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh database session per test."""
    engine = create_async_engine(
        TEST_DATABASE_URL, poolclass=NullPool, connect_args=_ENGINE_CONNECT_ARGS
    )
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

    await engine.dispose()


@pytest_asyncio.fixture
async def app(db_session: AsyncSession) -> FastAPI:
    """Return a FastAPI instance with test DB dependency override."""
    application = create_application()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client connected to the test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    return {
        "email": "testuser@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
    }
