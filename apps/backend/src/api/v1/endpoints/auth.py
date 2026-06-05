"""
Authentication API endpoints.
All routes are prefixed with /api/v1/auth
"""

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_auth_service, get_current_user
from src.db.engine import get_db
from src.db.models.user import User
from src.schemas.requests.auth import (
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from src.schemas.responses.auth import AuthResponse, TokenResponse, UserResponse
from src.services.auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Create a new user account and return an auth token pair.
    - Email must be unique
    - Password requires uppercase, lowercase, and digit
    """
    return await auth_service.register(payload)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    OAuth2-compatible login endpoint.
    Accepts form data with username (email) and password.
    Returns access and refresh tokens.
    """
    from src.schemas.requests.auth import LoginRequest

    payload = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )
    auth_response = await auth_service.login(payload)
    return auth_response.tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Rotate refresh token and issue new access token."""
    return await auth_service.refresh_tokens(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke refresh token",
)
async def logout(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    """Revoke the provided refresh token."""
    await auth_service.logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the authenticated user profile."""
    return current_user
