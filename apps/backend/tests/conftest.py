"""
Pytest configuration and shared fixtures.

Uses a test database with transaction rollback strategy
to keep tests isolated without resetting the schema.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.db.engine import get_db
from src.db.models.base import Base
from src.main import create_application

TEST_DATABASE_URL = (
    "postgresql+asyncpg://cip_user:cip_password@localhost:5432/cip_test"
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():  # type: ignore[no-untyped-def]
    """Create test engine once per session."""
    db_url = os.getenv("DATABASE_URL", TEST_DATABASE_URL)
    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[no-untyped-def]
    """
    Provide an isolated test database session.
    Each test runs inside a savepoint that is rolled back after the test.
    """
    session_factory = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as session, session.begin():
        yield session
        await session.rollback()


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


def pytest_configure(config: Any) -> None:  # type: ignore[no-untyped-def]
    """Configure structlog for testing to avoid PrintLogger.name errors."""
    import logging
    import structlog

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


def pytest_fixture_setup(fixturedef: Any, request: Any) -> None:
    pass


import pytest  # noqa: E402

@pytest.fixture
def test_user_data() -> dict[str, Any]:
    return {
        "email": "testuser@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
    }
