"""
Dropbox OAuth broker.

Same ticket/exchange staging design as GoogleDriveOAuthService — see that
module's docstring for the full rationale.

Unlike OneDrive, Dropbox has a straightforward token-revoke endpoint
(POST /2/auth/token/revoke, authenticated with the token being revoked),
so this service has a disconnect leg, structured just like Google's.
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
from src.schemas.responses.storage_oauth import DropboxTokenResponse

logger = get_logger(__name__)
_settings = get_settings()

_DROPBOX_AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
_DROPBOX_TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
_DROPBOX_REVOKE_URL = "https://api.dropboxapi.com/2/auth/token/revoke"

_TICKET_KEY_PREFIX = "dropbox:ticket:"
_EXCHANGE_KEY_PREFIX = "dropbox:exchange:"


class DropboxOAuthError(Exception):
    """Raised when the callback step itself fails (redirects, doesn't 500)."""

    def __init__(self, error_code: str) -> None:
        self.error_code = error_code
        super().__init__(error_code)


class DropboxOAuthService:
    """
    Handles connect -> callback -> exchange -> refresh -> disconnect for
    Dropbox. Structurally identical to GoogleDriveOAuthService; see that
    class for the leg-by-leg design rationale.
    """

    def __init__(self, redis: RedisLike) -> None:
        self.redis = redis

    def _require_configured(self) -> None:
        if not _settings.DROPBOX_CLIENT_ID or not _settings.DROPBOX_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Dropbox storage is not configured. Set DROPBOX_CLIENT_ID "
                    "and DROPBOX_CLIENT_SECRET."
                ),
            )

    # ── Leg 1: connect ───────────────────────────────────────────────────────

    async def create_authorize_url(self, user_id: UUID) -> str:
        self._require_configured()

        ticket_id = secrets.token_urlsafe(32)
        await self.redis.set(
            f"{_TICKET_KEY_PREFIX}{ticket_id}",
            str(user_id),
            ex=_settings.DROPBOX_TICKET_TTL_SECONDS,
        )

        params = {
            "client_id": _settings.DROPBOX_CLIENT_ID,
            "redirect_uri": _settings.DROPBOX_OAUTH_REDIRECT_URI,
            "response_type": "code",
            # Required to get a refresh_token back at all — Dropbox
            # defaults to short-lived-only access tokens otherwise.
            "token_access_type": "offline",
            "scope": " ".join(_settings.DROPBOX_SCOPES),
            "state": ticket_id,
        }
        return f"{_DROPBOX_AUTH_URL}?{urlencode(params)}"

    # ── Leg 2: callback ──────────────────────────────────────────────────────

    async def handle_callback(
        self,
        code: str | None,
        state: str | None,
        dropbox_error: str | None,
    ) -> str:
        """Same contract as GoogleDriveOAuthService.handle_callback."""
        try:
            if dropbox_error:
                logger.warning("Dropbox OAuth denied or errored", error=dropbox_error)
                raise DropboxOAuthError(dropbox_error)

            if not code or not state:
                raise DropboxOAuthError("missing_code_or_state")

            user_id = await self.redis.get(f"{_TICKET_KEY_PREFIX}{state}")
            if not user_id:
                raise DropboxOAuthError("invalid_or_expired_ticket")
            await self.redis.delete(f"{_TICKET_KEY_PREFIX}{state}")

            tokens = await self._exchange_code_with_dropbox(code)

            exchange_code = secrets.token_urlsafe(32)
            payload = {
                "user_id": user_id,
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token"),
                "scope": tokens.get("scope", " ".join(_settings.DROPBOX_SCOPES)),
                "expires_at": (
                    datetime.now(UTC) + timedelta(seconds=int(tokens["expires_in"]))
                ).isoformat(),
            }
            await self.redis.set(
                f"{_EXCHANGE_KEY_PREFIX}{exchange_code}",
                json.dumps(payload),
                ex=_settings.DROPBOX_EXCHANGE_TTL_SECONDS,
            )

            return self._frontend_redirect(dropbox_exchange=exchange_code)

        except DropboxOAuthError as exc:
            return self._frontend_redirect(dropbox_error=exc.error_code)

    async def _exchange_code_with_dropbox(self, code: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _DROPBOX_TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": _settings.DROPBOX_CLIENT_ID,
                        "client_secret": _settings.DROPBOX_CLIENT_SECRET,
                        "redirect_uri": _settings.DROPBOX_OAUTH_REDIRECT_URI,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Dropbox token exchange failed",
                status=exc.response.status_code,
                body=exc.response.text[:500],
            )
            raise DropboxOAuthError("token_exchange_failed") from exc
        except httpx.TimeoutException as exc:
            logger.error("Dropbox token exchange timed out")
            raise DropboxOAuthError("token_exchange_timeout") from exc

        data: dict[str, Any] = response.json()
        if "access_token" not in data or "expires_in" not in data:
            raise DropboxOAuthError("malformed_token_response")
        return data

    @staticmethod
    def _frontend_redirect(
        *,
        dropbox_exchange: str | None = None,
        dropbox_error: str | None = None,
    ) -> str:
        params = {"tab": "storage"}
        if dropbox_exchange:
            params["dropbox_exchange"] = dropbox_exchange
        if dropbox_error:
            params["dropbox_error"] = dropbox_error
        return f"{_settings.FRONTEND_URL}/settings?{urlencode(params)}"

    # ── Leg 3: exchange ──────────────────────────────────────────────────────

    async def claim_exchange(self, user_id: UUID, exchange_code: str) -> DropboxTokenResponse:
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

        return DropboxTokenResponse(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            scope=payload["scope"],
        )

    # ── Leg 4: refresh ───────────────────────────────────────────────────────

    async def refresh_access_token(self, refresh_token: str) -> DropboxTokenResponse:
        self._require_configured()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _DROPBOX_TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": _settings.DROPBOX_CLIENT_ID,
                        "client_secret": _settings.DROPBOX_CLIENT_SECRET,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Dropbox token refresh failed",
                status=exc.response.status_code,
                body=exc.response.text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not refresh Dropbox access. Please reconnect.",
            ) from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Dropbox refresh timed out. Please try again.",
            ) from exc

        data = response.json()
        return DropboxTokenResponse(
            access_token=data["access_token"],
            # Dropbox doesn't return a new refresh_token on /refresh —
            # the original one keeps working until explicitly revoked.
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.now(UTC) + timedelta(seconds=int(data["expires_in"])),
            scope=data.get("scope", " ".join(_settings.DROPBOX_SCOPES)),
        )

    # ── Disconnect ───────────────────────────────────────────────────────────

    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoke an access token at Dropbox. Unlike Google's revoke (which
        takes the token as a body param and works for either token type),
        Dropbox's endpoint authenticates *as* the token being revoked —
        pass an access token, not a refresh token.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _DROPBOX_REVOKE_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Dropbox disconnect timed out. Please try again.",
            ) from exc

        if response.status_code in (200, 401):
            # 401 typically means the token was already invalid/expired
            # — functionally revoked either way.
            return True

        logger.error(
            "Dropbox token revoke failed",
            status=response.status_code,
            body=response.text[:500],
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not disconnect Dropbox. Please try again.",
        )
