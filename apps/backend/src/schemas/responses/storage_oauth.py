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


class OneDriveConnectResponse(BaseModel):
    """Response from GET /storage/onedrive/connect."""

    authorize_url: str


class OneDriveTokenResponse(BaseModel):
    """
    Response from POST /storage/onedrive/exchange and
    POST /storage/onedrive/refresh. Same shape/purpose as
    GoogleDriveTokenResponse — see that docstring.
    """

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime
    scope: str


class DropboxConnectResponse(BaseModel):
    """Response from GET /storage/dropbox/connect."""

    authorize_url: str


class DropboxTokenResponse(BaseModel):
    """
    Response from POST /storage/dropbox/exchange and
    POST /storage/dropbox/refresh. Same shape/purpose as
    GoogleDriveTokenResponse — see that docstring.
    """

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime
    scope: str


class DropboxDisconnectResponse(BaseModel):
    """Response from POST /storage/dropbox/disconnect."""

    revoked: bool
