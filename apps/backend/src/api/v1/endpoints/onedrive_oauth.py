"""
BYOS OneDrive OAuth broker endpoints.

Four endpoints implementing connect -> callback -> exchange -> refresh
(see src/services/storage_oauth/onedrive_oauth_service.py). Unlike the
Google Drive broker, there is no /disconnect endpoint here: Microsoft's
v2.0 endpoint has no simple per-token revoke API for this flow.
Disconnecting OneDrive is handled entirely client-side — the frontend
clears its stored tokens and stops calling the Graph API. See
docs/architecture/byos.md.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from src.api.v1.dependencies.auth import get_current_user
from src.core.cache.redis_client import RedisLike, get_redis
from src.db.models.user import User
from src.schemas.requests.storage_oauth import OneDriveExchangeRequest, OneDriveRefreshRequest
from src.schemas.responses.storage_oauth import OneDriveConnectResponse, OneDriveTokenResponse
from src.services.storage_oauth.onedrive_oauth_service import OneDriveOAuthService

router = APIRouter(prefix="/storage/onedrive", tags=["Storage — OneDrive (BYOS)"])


async def get_onedrive_oauth_service(
    redis: RedisLike = Depends(get_redis),
) -> OneDriveOAuthService:
    return OneDriveOAuthService(redis)


@router.get(
    "/connect",
    response_model=OneDriveConnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a OneDrive connect flow",
    description=(
        "Stages a short-lived ticket binding this connect attempt to the "
        "current user, and returns the Microsoft authorization URL the "
        "frontend should navigate the browser to."
    ),
)
async def connect(
    current_user: User = Depends(get_current_user),
    service: OneDriveOAuthService = Depends(get_onedrive_oauth_service),
) -> OneDriveConnectResponse:
    authorize_url = await service.create_authorize_url(current_user.id)
    return OneDriveConnectResponse(authorize_url=authorize_url)


@router.get(
    "/callback",
    status_code=status.HTTP_302_FOUND,
    summary="Microsoft's OAuth redirect target",
    description=(
        "Not called by the frontend directly — this is where Microsoft "
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
    service: OneDriveOAuthService = Depends(get_onedrive_oauth_service),
) -> RedirectResponse:
    redirect_url = await service.handle_callback(code=code, state=state, microsoft_error=error)
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post(
    "/exchange",
    response_model=OneDriveTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Claim tokens staged by the callback",
    description=(
        "Single-use: the exchange code is deleted the moment it's claimed. "
        "The returned tokens are handed to the browser and never persisted "
        "server-side."
    ),
)
async def exchange(
    payload: OneDriveExchangeRequest,
    current_user: User = Depends(get_current_user),
    service: OneDriveOAuthService = Depends(get_onedrive_oauth_service),
) -> OneDriveTokenResponse:
    return await service.claim_exchange(current_user.id, payload.exchange_code)


@router.post(
    "/refresh",
    response_model=OneDriveTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an expired OneDrive access token",
)
async def refresh(
    payload: OneDriveRefreshRequest,
    current_user: User = Depends(get_current_user),
    service: OneDriveOAuthService = Depends(get_onedrive_oauth_service),
) -> OneDriveTokenResponse:
    return await service.refresh_access_token(payload.refresh_token)
