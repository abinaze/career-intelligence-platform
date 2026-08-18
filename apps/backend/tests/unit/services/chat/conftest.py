"""
Local conftest for unit/services/chat tests.

These are pure unit tests against llm_provider.py with mocked httpx
calls to Anthropic — no database access needed. Override both
setup_database and clean_tables as no-ops so the root autouse fixture
does not attempt a Postgres connection (see
tests/unit/services/storage_oauth/conftest.py and tests/unit/ai/conftest.py
for the identical, established pattern).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest


@pytest.fixture(scope="session")
async def setup_database() -> None:  # type: ignore[override]
    """No-op: chat provider unit tests do not require a database."""
    yield  # type: ignore[misc]


@pytest.fixture(autouse=True)
async def clean_tables(setup_database: None) -> AsyncGenerator[None, None]:  # type: ignore[override]
    """No-op: chat provider unit tests do not require table truncation."""
    yield
