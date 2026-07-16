"""
Async Redis client for short-lived cache/staging keys.

This is intentionally narrow — it is used only for ephemeral OAuth
handshake staging (see src/services/storage_oauth/), never for personal
user data. See docs/architecture/byos.md for why.

All access should go through get_redis() so tests can override the
dependency the same way get_db() is overridden.
"""

from __future__ import annotations

from typing import Protocol, cast

from redis.asyncio import Redis

from src.core.config.settings import get_settings

_settings = get_settings()


class RedisLike(Protocol):
    """
    The minimal subset of the Redis async API this project relies on.

    Defined as a Protocol (rather than importing the real client type
    everywhere) so unit tests can pass a small hand-written in-memory fake
    instead of pulling in a real Redis server or the `fakeredis` package —
    consistent with this project's existing dependency discipline.
    """

    async def set(
        self,
        name: str,
        value: str,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool | None: ...

    async def get(self, name: str) -> str | None: ...

    async def delete(self, *names: str) -> int: ...

    async def exists(self, *names: str) -> int: ...


_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """Return the process-level singleton Redis client, creating it lazily."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            _settings.REDIS_URL,
            decode_responses=True,
            max_connections=_settings.REDIS_MAX_CONNECTIONS,
        )
    return _redis_client


async def get_redis() -> RedisLike:
    """FastAPI dependency that provides the shared Redis client."""
    # redis-py's stubs accept the broader `bytes | str | memoryview` for key
    # names, which is why Redis doesn't structurally satisfy our narrower,
    # str-only RedisLike Protocol without a cast — behavior for str
    # arguments (the only kind this project ever passes) is identical.
    return cast(RedisLike, get_redis_client())


async def check_redis_connection() -> bool:
    """Health check: verify Redis connectivity."""
    try:
        client = get_redis_client()
        return bool(await client.ping())
    except Exception:
        return False
