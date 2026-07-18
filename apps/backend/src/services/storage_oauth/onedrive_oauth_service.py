"""
OneDrive OAuth broker.

Same ticket/exchange staging design as GoogleDriveOAuthService (see that
module's docstring for the full rationale) — brokers the Microsoft OAuth
handshake without ever persisting the resulting tokens server-side.

One real difference from Google Drive: Microsoft's v2.0 endpoint has no
simple per-token revoke API for this flow (no equivalent of Google's
POST /revoke that just takes a token and invalidates it). Because of
that, there's no `revoke_token()` method here and no
`/storage/onedrive/disconnect` endpoint — disconnecting is handled
entirely client-side (the frontend clears its stored tokens and stops
calling the Graph API; the token itself simply expires and won't be
refreshed again). A user who wants to fully revoke access needs to do it
from their Microsoft account's app permissions page — this is documented
in docs/setup/microsoft-oauth-setup.md and the API reference, not hidden.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import secrets
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from fastapi import HTTPException, status
import httpx

from src.core.cache.redis_client import RedisLike
from src.core.config.settings import get_settings
from src.core.logging.setup import get_logger
from src.schemas.responses.storage_oauth import OneDriveTokenResponse

logger = get_logger(__name__)
_settings = get_settings()

_TICKET_KEY_PREFIX = "onedrive:ticket:"
_EXCHANGE_KEY_PREFIX = "onedrive:exchange:"


def _authorize_url() -> str:
    return f"https://login.microsoftonline.com/{_settings.MICROSOFT_OAUTH_TENANT}/oauth2/v2.0/authorize"


def _token_url() -> str:
    return f"https://login.microsoftonline.com/{_settings.MICROSOFT_OAUTH_TENANT}/oauth2/v2.0/token"


class OneDriveOAuthError(Exception):
    """Raised when the callback step itself fails (redirects, doesn't 500)."""

    def __init__(self, error_code: str) -> None:
        self.error_code = error_code
        super().__init__(error_code)


class OneDriveOAuthService:
    """
    Handles connect -> callback -> exchange -> refresh for OneDrive.
    Structurally identical to GoogleDriveOAuthService; see that class for
    the leg-by-leg design rationale. Differences are Microsoft-specific
    endpoint shapes and the absence of a disconnect/revoke leg.
    """

    def __init__(self, redis: RedisLike) -> None:
        self.redis = redis

    def _require_configured(self) -> None:
        if not _settings.MICROSOFT_CLIENT_ID or not _settings.MICROSOFT_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "OneDrive storage is not configured. Set MICROSOFT_CLIENT_ID "
                    "and MICROSOFT_CLIENT_SECRET."
                ),
            )

    # ── Leg 1: connect ───────────────────────────────────────────────────────

    async def create_authorize_url(self, user_id: UUID) -> str:
        self._require_configured()

        ticket_id = secrets.token_urlsafe(32)
        await self.redis.set(
            f"{_TICKET_KEY_PREFIX}{ticket_id}",
            str(user_id),
            ex=_settings.MICROSOFT_ONEDRIVE_TICKET_TTL_SECONDS,
        )

        params = {
            "client_id": _settings.MICROSOFT_CLIENT_ID,
            "redirect_uri": _settings.MICROSOFT_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "response_mode": "query",
            "scope": " ".join(_settings.MICROSOFT_ONEDRIVE_SCOPES),
            "state": ticket_id,
        }
        return f"{_authorize_url()}?{urlencode(params)}"

    # ── Leg 2: callback ──────────────────────────────────────────────────────

    async def handle_callback(
        self,
        code: str | None,
        state: str | None,
        microsoft_error: str | None,
    ) -> str:
        """Same contract as GoogleDriveOAuthService.handle_callback."""
        try:
            if microsoft_error:
                logger.warning("OneDrive OAuth denied or errored", error=microsoft_error)
                raise OneDriveOAuthError(microsoft_error)

            if not code or not state:
                raise OneDriveOAuthError("missing_code_or_state")

            user_id = await self.redis.get(f"{_TICKET_KEY_PREFIX}{state}")
            if not user_id:
                raise OneDriveOAuthError("invalid_or_expired_ticket")
            await self.redis.delete(f"{_TICKET_KEY_PREFIX}{state}")

            tokens = await self._exchange_code_with_microsoft(code)

            exchange_code = secrets.token_urlsafe(32)
            payload = {
                "user_id": user_id,
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token"),
                "scope": tokens.get("scope", " ".join(_settings.MICROSOFT_ONEDRIVE_SCOPES)),
                "expires_at": (
                    datetime.now(UTC) + timedelta(seconds=int(tokens["expires_in"]))
                ).isoformat(),
            }
            await self.redis.set(
                f"{_EXCHANGE_KEY_PREFIX}{exchange_code}",
                json.dumps(payload),
                ex=_settings.MICROSOFT_ONEDRIVE_EXCHANGE_TTL_SECONDS,
            )

            return self._frontend_redirect(onedrive_exchange=exchange_code)

        except OneDriveOAuthError as exc:
            return self._frontend_redirect(onedrive_error=exc.error_code)

    async def _exchange_code_with_microsoft(self, code: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _token_url(),
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": _settings.MICROSOFT_CLIENT_ID,
                        "client_secret": _settings.MICROSOFT_CLIENT_SECRET,
                        "redirect_uri": _settings.MICROSOFT_OAUTH_REDIRECT_URI,
                        "scope": " ".join(_settings.MICROSOFT_ONEDRIVE_SCOPES),
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Microsoft token exchange failed",
                status=exc.response.status_code,
                body=exc.response.text[:500],
            )
            raise OneDriveOAuthError("token_exchange_failed") from exc
        except httpx.TimeoutException as exc:
            logger.error("Microsoft token exchange timed out")
            raise OneDriveOAuthError("token_exchange_timeout") from exc

        data: dict[str, Any] = response.json()
        if "access_token" not in data or "expires_in" not in data:
            raise OneDriveOAuthError("malformed_token_response")
        return data

    @staticmethod
    def _frontend_redirect(
        *,
        onedrive_exchange: str | None = None,
        onedrive_error: str | None = None,
    ) -> str:
        params = {"tab": "storage"}
        if onedrive_exchange:
            params["onedrive_exchange"] = onedrive_exchange
        if onedrive_error:
            params["onedrive_error"] = onedrive_error
        return f"{_settings.FRONTEND_URL}/settings?{urlencode(params)}"

    # ── Leg 3: exchange ──────────────────────────────────────────────────────

    async def claim_exchange(self, user_id: UUID, exchange_code: str) -> OneDriveTokenResponse:
        key = f"{_EXCHANGE_KEY_PREFIX}{exchange_code}"
        raw = await self.redis.get(key)
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange code is invalid or has expired. Please reconnect.",
            )
        await self.redis.delete(key)

        payload = json.loads(raw)
        if payload["user_id"] != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This exchange code does not belong to your account.",
            )

        return OneDriveTokenResponse(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            scope=payload["scope"],
        )

    # ── Leg 4: refresh ───────────────────────────────────────────────────────

    async def refresh_access_token(self, refresh_token: str) -> OneDriveTokenResponse:
        self._require_configured()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _token_url(),
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": _settings.MICROSOFT_CLIENT_ID,
                        "client_secret": _settings.MICROSOFT_CLIENT_SECRET,
                        "scope": " ".join(_settings.MICROSOFT_ONEDRIVE_SCOPES),
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Microsoft token refresh failed",
                status=exc.response.status_code,
                body=exc.response.text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not refresh OneDrive access. Please reconnect.",
            ) from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="OneDrive refresh timed out. Please try again.",
            ) from exc

        data = response.json()
        return OneDriveTokenResponse(
            access_token=data["access_token"],
            # Microsoft always rotates the refresh token on use — unlike
            # Google, it's not optional to check for; still guard with
            # .get() in case a future response shape omits it.
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.now(UTC) + timedelta(seconds=int(data["expires_in"])),
            scope=data.get("scope", " ".join(_settings.MICROSOFT_ONEDRIVE_SCOPES)),
        )
