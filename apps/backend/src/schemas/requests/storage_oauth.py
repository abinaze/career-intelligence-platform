"""Request schemas for the BYOS Google Drive OAuth broker endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GoogleDriveExchangeRequest(BaseModel):
    """Body for POST /storage/google-drive/exchange.

    The exchange_code is the single-use, 60-second-TTL code staged by the
    callback endpoint — never the raw Google authorization code, and never
    the tokens themselves (those only ever travel over this authenticated
    POST, not a URL).
    """

    exchange_code: str = Field(..., min_length=1, max_length=256)


class GoogleDriveRefreshRequest(BaseModel):
    """Body for POST /storage/google-drive/refresh."""

    refresh_token: str = Field(..., min_length=1)


class GoogleDriveDisconnectRequest(BaseModel):
    """Body for POST /storage/google-drive/disconnect.

    Either token can be supplied — Google's revoke endpoint accepts an
    access token or a refresh token and invalidates the associated grant.
    """

    token: str = Field(..., min_length=1)
