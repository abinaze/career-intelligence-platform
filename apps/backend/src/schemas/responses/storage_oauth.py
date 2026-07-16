"""Response schemas for the BYOS Google Drive OAuth broker endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class GoogleDriveConnectResponse(BaseModel):
    """Response from GET /storage/google-drive/connect."""

    authorize_url: str


class GoogleDriveTokenResponse(BaseModel):
    """
    Response from POST /storage/google-drive/exchange and
    POST /storage/google-drive/refresh.

    Handed to the browser once and never persisted server-side. The
    frontend stores these in the same IndexedDB store LocalDeviceAdapter
    already uses, under distinct keys (see features/storage/adapters/).
    """

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime
    scope: str


class GoogleDriveDisconnectResponse(BaseModel):
    """Response from POST /storage/google-drive/disconnect."""

    revoked: bool
