"""
Local conftest for unit/services/storage_oauth tests.

These are pure unit tests against GoogleDriveOAuthService with a
hand-written in-memory FakeRedis and mocked httpx calls to Google — no
database access needed. Override both setup_database and clean_tables as
no-ops so the root autouse fixture does not attempt a Postgres connection
(see tests/unit/ai/conftest.py for the identical, established pattern).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from tests.unit.services.storage_oauth.fakes import FakeRedis


@pytest.fixture(scope="session")
async def setup_database() -> None:  # type: ignore[override]
    """No-op: storage_oauth unit tests do not require a database."""
    yield  # type: ignore[misc]


@pytest.fixture(autouse=True)
async def clean_tables(setup_database: None) -> AsyncGenerator[None, None]:  # type: ignore[override]
    """No-op: storage_oauth unit tests do not require table truncation."""
    yield


@pytest.fixture
def fake_redis() -> FakeRedis:
    """A fresh in-memory fake Redis per test."""
    return FakeRedis()
