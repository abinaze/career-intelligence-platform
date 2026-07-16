"""
BYOS Google Drive OAuth broker endpoints.

Five endpoints implementing the connect -> callback -> exchange -> refresh
(+ disconnect) flow described in src/services/storage_oauth/. The backend
never stores the resulting tokens — see docs/architecture/byos.md.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from src.api.v1.dependencies.auth import get_current_user
from src.core.cache.redis_client import RedisLike, get_redis
from src.db.models.user import User
from src.schemas.requests.storage_oauth import (
    GoogleDriveDisconnectRequest,
    GoogleDriveExchangeRequest,
    GoogleDriveRefreshRequest,
)
from src.schemas.responses.storage_oauth import (
    GoogleDriveConnectResponse,
    GoogleDriveDisconnectResponse,
    GoogleDriveTokenResponse,
)
from src.services.storage_oauth.google_oauth_service import GoogleDriveOAuthService

router = APIRouter(prefix="/storage/google-drive", tags=["Storage — Google Drive (BYOS)"])


async def get_google_oauth_service(
    redis: RedisLike = Depends(get_redis),
) -> GoogleDriveOAuthService:
    return GoogleDriveOAuthService(redis)


@router.get(
    "/connect",
    response_model=GoogleDriveConnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a Google Drive connect flow",
    description=(
        "Stages a short-lived ticket binding this connect attempt to the "
        "current user, and returns the Google authorization URL the "
        "frontend should navigate the browser to."
    ),
)
async def connect(
    current_user: User = Depends(get_current_user),
    service: GoogleDriveOAuthService = Depends(get_google_oauth_service),
) -> GoogleDriveConnectResponse:
    authorize_url = await service.create_authorize_url(current_user.id)
    return GoogleDriveConnectResponse(authorize_url=authorize_url)


@router.get(
    "/callback",
    status_code=status.HTTP_302_FOUND,
    summary="Google's OAuth redirect target",
    description=(
        "Not called by the frontend directly — this is where Google "
        "redirects the browser after the user approves or denies access. "
        "Always redirects onward to the frontend settings page, either "
        "with a claimable exchange code or an error flag."
    ),
    include_in_schema=False,
)
async def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    service: GoogleDriveOAuthService = Depends(get_google_oauth_service),
) -> RedirectResponse:
    redirect_url = await service.handle_callback(code=code, state=state, google_error=error)
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post(
    "/exchange",
    response_model=GoogleDriveTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Claim tokens staged by the callback",
    description=(
        "Single-use: the exchange code is deleted the moment it's claimed. "
        "The returned tokens are handed to the browser and never persisted "
        "server-side — store them in IndexedDB alongside local-device data."
    ),
)
async def exchange(
    payload: GoogleDriveExchangeRequest,
    current_user: User = Depends(get_current_user),
    service: GoogleDriveOAuthService = Depends(get_google_oauth_service),
) -> GoogleDriveTokenResponse:
    return await service.claim_exchange(current_user.id, payload.exchange_code)


@router.post(
    "/refresh",
    response_model=GoogleDriveTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an expired Google Drive access token",
)
async def refresh(
    payload: GoogleDriveRefreshRequest,
    current_user: User = Depends(get_current_user),
    service: GoogleDriveOAuthService = Depends(get_google_oauth_service),
) -> GoogleDriveTokenResponse:
    return await service.refresh_access_token(payload.refresh_token)


@router.post(
    "/disconnect",
    response_model=GoogleDriveDisconnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a Google Drive token at Google",
    description=(
        "Revokes the supplied access or refresh token at Google. The "
        "frontend is responsible for clearing its locally-stored copy "
        "regardless of this call's outcome."
    ),
)
async def disconnect(
    payload: GoogleDriveDisconnectRequest,
    current_user: User = Depends(get_current_user),
    service: GoogleDriveOAuthService = Depends(get_google_oauth_service),
) -> GoogleDriveDisconnectResponse:
    revoked = await service.revoke_token(payload.token)
    return GoogleDriveDisconnectResponse(revoked=revoked)
