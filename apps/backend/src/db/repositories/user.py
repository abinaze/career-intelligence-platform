"""User-specific database queries."""

from __future__ import annotations

import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.user import RefreshToken, User
from src.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by email address."""
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower().strip())
            .options(selectinload(User.profile))
        )
        return result.scalar_one_or_none()

    async def get_with_profile(self, user_id: object) -> User | None:
        """Fetch user with eagerly loaded profile."""
        result = await self.db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.profile))
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        result = await self.db.execute(select(User.id).where(User.email == email.lower().strip()))
        return result.scalar_one_or_none() is not None

    async def update_last_login(self, user_id: object) -> None:
        """Record login timestamp."""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.datetime.now(tz=datetime.UTC))
        )
        await self.db.flush()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(RefreshToken, db)

    async def get_valid_token(self, token_hash: str) -> RefreshToken | None:
        """Fetch a non-revoked, non-expired refresh token."""
        now = datetime.datetime.now(tz=datetime.UTC)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def revoke_all_user_tokens(self, user_id: object) -> None:
        """Revoke all refresh tokens for a user."""
        now = datetime.datetime.now(tz=datetime.UTC)
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
            .values(is_revoked=True, revoked_at=now)
        )
        await self.db.flush()

    async def revoke_token(self, token_hash: str) -> None:
        """Revoke a specific token by its hash."""
        now = datetime.datetime.now(tz=datetime.UTC)
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True, revoked_at=now)
        )
        await self.db.flush()
