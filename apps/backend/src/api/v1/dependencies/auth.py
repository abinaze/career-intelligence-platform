"""
FastAPI authentication dependencies.

These are injected into route handlers to:
- validate JWT access tokens
- enforce role-based access control
- provide the current authenticated user
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging.setup import get_logger
from src.core.security.jwt import decode_access_token
from src.db.engine import get_db
from src.db.models.user import User, UserRole
from src.services.auth.auth_service import AuthService

logger = get_logger(__name__)

http_bearer = HTTPBearer(auto_error=True)


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """Provide an AuthService instance scoped to the current request."""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Validate JWT and return the current authenticated user.

    Usage in route handlers:
        @router.get("/me")
        async def get_me(user: User = Depends(get_current_user)):
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id_str: str = payload.get("sub", "")
        if not user_id_str:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError) as err:
        raise credentials_exception from err

    user = await auth_service.get_current_user(user_id)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


def require_role(*roles: UserRole):  # type: ignore[no-untyped-def]
    """Role-based access control dependency factory."""

    async def _check_role(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return _check_role
