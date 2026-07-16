"""
Minimal in-memory fake Redis for unit tests.

Implements just the subset of the async Redis API GoogleDriveOAuthService
actually uses (set/get/delete/exists, with `ex` TTL support). Written by
hand rather than pulling in the `fakeredis` package, consistent with this
project's existing dependency discipline (see the handover doc's note on
preferring short hand-written implementations over small utility deps).
"""

from __future__ import annotations

import time


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._expires_at: dict[str, float] = {}

    def _is_expired(self, name: str) -> bool:
        expiry = self._expires_at.get(name)
        return expiry is not None and expiry <= time.monotonic()

    def _evict_if_expired(self, name: str) -> None:
        if self._is_expired(name):
            self._store.pop(name, None)
            self._expires_at.pop(name, None)

    async def set(
        self,
        name: str,
        value: str,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool | None:
        self._evict_if_expired(name)
        if nx and name in self._store:
            return None
        self._store[name] = value
        if ex is not None:
            self._expires_at[name] = time.monotonic() + ex
        else:
            self._expires_at.pop(name, None)
        return True

    async def get(self, name: str) -> str | None:
        self._evict_if_expired(name)
        return self._store.get(name)

    async def delete(self, *names: str) -> int:
        deleted = 0
        for name in names:
            self._evict_if_expired(name)
            if name in self._store:
                del self._store[name]
                self._expires_at.pop(name, None)
                deleted += 1
        return deleted

    async def exists(self, *names: str) -> int:
        count = 0
        for name in names:
            self._evict_if_expired(name)
            if name in self._store:
                count += 1
        return count

    # Test-only helper: simulate TTL expiry without a real sleep.
    def force_expire(self, name: str) -> None:
        if name in self._store:
            self._expires_at[name] = time.monotonic() - 1
