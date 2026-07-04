"""
Local conftest for unit/ai tests.

These tests are pure unit tests with no database access needed.
Override both setup_database and clean_tables to no-ops so the
autouse fixture does not attempt a Postgres connection.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest


@pytest.fixture(scope="session")
async def setup_database() -> None:  # type: ignore[override]
    """No-op: AI unit tests do not require a database."""
    yield  # type: ignore[misc]


@pytest.fixture(autouse=True)
async def clean_tables(setup_database: None) -> AsyncGenerator[None, None]:  # type: ignore[override]
    """No-op: AI unit tests do not require table truncation."""
    yield
