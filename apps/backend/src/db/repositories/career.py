"""Repository for Career occupation records."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.career import Career
from src.db.repositories.base import BaseRepository


class CareerRepository(BaseRepository[Career]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Career, db)

    async def get_by_onet_code(self, onet_code: str) -> Career | None:
        """Fetch a single career by its O*NET occupation code."""
        result = await self.db.execute(select(Career).where(Career.onet_code == onet_code))
        return result.scalar_one_or_none()

    async def search_by_title(self, query: str, limit: int = 20) -> list[Career]:
        """Case-insensitive title search."""
        result = await self.db.execute(
            select(Career)
            .where(Career.title.ilike(f"%{query}%"))
            .order_by(Career.title)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(self, broad_category: str, limit: int = 50) -> list[Career]:
        """Return careers within a broad O*NET category."""
        result = await self.db.execute(
            select(Career)
            .where(Career.broad_category == broad_category)
            .order_by(Career.outlook_percentile.desc().nulls_last())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_paginated(self, offset: int = 0, limit: int = 100) -> list[Career]:
        """Return paginated career records ordered by title."""
        result = await self.db.execute(
            select(Career).order_by(Career.title).offset(offset).limit(limit)
        )
        return list(result.scalars().all())
