"""
BYOS Dropbox OAuth broker endpoints.

Five endpoints implementing connect -> callback -> exchange -> refresh
(+ disconnect) — same shape as the Google Drive broker, since Dropbox
(unlike OneDrive) has a real token-revoke endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from src.api.v1.dependencies.auth import get_current_user
from src.core.cache.redis_client import RedisLike, get_redis
from src.db.models.user import User
from src.schemas.requests.storage_oauth import (
    DropboxDisconnectRequest,
    DropboxExchangeRequest,
    DropboxRefreshRequest,
)
from src.schemas.responses.storage_oauth import (
    DropboxConnectResponse,
    DropboxDisconnectResponse,
    DropboxTokenResponse,
)
from src.services.storage_oauth.dropbox_oauth_service import DropboxOAuthService

router = APIRouter(prefix="/storage/dropbox", tags=["Storage — Dropbox (BYOS)"])


async def get_dropbox_oauth_service(
    redis: RedisLike = Depends(get_redis),
) -> DropboxOAuthService:
    return DropboxOAuthService(redis)


@router.get(
    "/connect",
    response_model=DropboxConnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a Dropbox connect flow",
)
async def connect(
    current_user: User = Depends(get_current_user),
    service: DropboxOAuthService = Depends(get_dropbox_oauth_service),
) -> DropboxConnectResponse:
    authorize_url = await service.create_authorize_url(current_user.id)
    return DropboxConnectResponse(authorize_url=authorize_url)


@router.get(
    "/callback",
    status_code=status.HTTP_302_FOUND,
    summary="Dropbox's OAuth redirect target",
    description=(
        "Not called by the frontend directly — this is where Dropbox "
        "redirects the browser after the user approves or denies access."
    ),
    include_in_schema=False,
)
async def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    service: DropboxOAuthService = Depends(get_dropbox_oauth_service),
) -> RedirectResponse:
    redirect_url = await service.handle_callback(code=code, state=state, dropbox_error=error)
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post(
    "/exchange",
    response_model=DropboxTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Claim tokens staged by the callback",
)
async def exchange(
    payload: DropboxExchangeRequest,
    current_user: User = Depends(get_current_user),
    service: DropboxOAuthService = Depends(get_dropbox_oauth_service),
) -> DropboxTokenResponse:
    return await service.claim_exchange(current_user.id, payload.exchange_code)


@router.post(
    "/refresh",
    response_model=DropboxTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an expired Dropbox access token",
)
async def refresh(
    payload: DropboxRefreshRequest,
    current_user: User = Depends(get_current_user),
    service: DropboxOAuthService = Depends(get_dropbox_oauth_service),
) -> DropboxTokenResponse:
    return await service.refresh_access_token(payload.refresh_token)


@router.post(
    "/disconnect",
    response_model=DropboxDisconnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a Dropbox token at Dropbox",
)
async def disconnect(
    payload: DropboxDisconnectRequest,
    current_user: User = Depends(get_current_user),
    service: DropboxOAuthService = Depends(get_dropbox_oauth_service),
) -> DropboxDisconnectResponse:
    revoked = await service.revoke_token(payload.token)
    return DropboxDisconnectResponse(revoked=revoked)
