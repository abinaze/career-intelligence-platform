"""
Authentication business logic.

This service owns all auth flows: register, login, token refresh,
and logout. It coordinates between repositories and the security layer.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging.setup import get_logger
from src.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from src.core.config.settings import get_settings
from src.db.models.user import User, UserRole
from src.db.models.profile import UserProfile
from src.db.repositories.user import RefreshTokenRepository, UserRepository
from src.schemas.requests.auth import LoginRequest, RegisterRequest
from src.schemas.responses.auth import AuthResponse, TokenResponse

logger = get_logger(__name__)
_settings = get_settings()


class AuthService:
    """
    Handles all authentication and authorization operations.
    Designed to be instantiated per-request via FastAPI DI.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        """
        Register a new user account.
        Creates user + profile + issues initial token pair.
        Raises 409 if email already exists.
        """
        email = payload.email.lower().strip()

        if await self.user_repo.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        hashed = hash_password(payload.password)

        user = await self.user_repo.create(
            email=email,
            full_name=payload.full_name.strip(),
            hashed_password=hashed,
            role=UserRole.USER.value,
            is_active=True,
            is_verified=False,
        )

        profile = UserProfile(user_id=user.id)
        self.db.add(profile)
        await self.db.flush()

        logger.info(
            "New user registered",
            user_id=str(user.id),
            email=email,
        )

        tokens = await self._issue_token_pair(user)
        return AuthResponse(user=user, tokens=tokens)

    async def login(self, payload: LoginRequest) -> AuthResponse:
        """
        Authenticate user with email and password.
        Issues fresh token pair on success.
        Raises 401 on invalid credentials.
        """
        email = payload.email.lower().strip()
        user = await self.user_repo.get_by_email(email)

        if not user or not verify_password(
            payload.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated",
            )

        await self.user_repo.update_last_login(user.id)
        tokens = await self._issue_token_pair(user)

        logger.info("User logged in", user_id=str(user.id))
        return AuthResponse(user=user, tokens=tokens)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Rotate refresh token and issue new access token.
        Old refresh token is revoked immediately.
        Raises 401 if token is invalid, expired, or revoked.
        """
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        token_hash = hash_token(refresh_token)
        stored_token = await self.token_repo.get_valid_token(token_hash)

        if not stored_token:
            user_id = payload.get("sub")
            if user_id:
                await self.token_repo.revoke_all_user_tokens(user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        user = await self.user_repo.get_by_id(UUID(payload["sub"]))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )

        await self.token_repo.revoke_token(token_hash)
        return await self._issue_token_pair(user)

    async def logout(self, refresh_token: str) -> None:
        """Revoke the provided refresh token."""
        token_hash = hash_token(refresh_token)
        await self.token_repo.revoke_token(token_hash)

    async def get_current_user(self, user_id: UUID) -> User:
        """Fetch the authenticated user. Used by auth dependency."""
        user = await self.user_repo.get_with_profile(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def _issue_token_pair(self, user: User) -> TokenResponse:
        """Create and store a new access + refresh token pair."""
        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)

        token_hash = hash_token(refresh_token)
        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            days=_settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.token_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
