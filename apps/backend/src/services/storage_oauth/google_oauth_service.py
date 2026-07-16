"""
Google Drive OAuth broker.

Brokers the OAuth handshake for BYOS "Google Drive" storage without ever
persisting the resulting tokens server-side. See
docs/architecture/byos.md for the full design rationale; the short version:

- The Google client *secret* can't live in browser JS, so the backend has
  to be involved in the authorization-code exchange and refresh steps.
- Nothing requires the backend to *keep* the tokens afterwards. Once
  they're handed to the browser, the browser talks to the Drive REST API
  directly (see the frontend's googleDriveClient.ts).

Two short-lived Redis-staged secrets make this handoff safe:

1. A **ticket** (default 5 min TTL) binds "a connect flow is underway" to
   a user_id across the Google redirect, which is a plain browser
   navigation with no Authorization header attached.
2. An **exchange code** (default 60s TTL) stages the freshly-issued tokens
   right after Google's callback so they never travel through a URL query
   string — the frontend claims them once over an authenticated POST, and
   the code is deleted immediately after (single use).
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
from src.schemas.responses.storage_oauth import GoogleDriveTokenResponse

logger = get_logger(__name__)
_settings = get_settings()

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

_TICKET_KEY_PREFIX = "gdrive:ticket:"
_EXCHANGE_KEY_PREFIX = "gdrive:exchange:"


class GoogleDriveOAuthError(Exception):
    """Raised when the callback step itself fails (redirects, doesn't 500s)."""

    def __init__(self, error_code: str) -> None:
        self.error_code = error_code
        super().__init__(error_code)


class GoogleDriveOAuthService:
    """
    Handles the four legs of the Google Drive BYOS OAuth flow:
    connect -> callback -> exchange -> refresh (+ disconnect).

    Instantiated per-request via FastAPI DI, like the other services —
    but holds no database session, only a Redis handle for the short-lived
    staging keys described above.
    """

    def __init__(self, redis: RedisLike) -> None:
        self.redis = redis

    def _require_configured(self) -> None:
        if not _settings.GOOGLE_CLIENT_ID or not _settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Google Drive storage is not configured. Set GOOGLE_CLIENT_ID "
                    "and GOOGLE_CLIENT_SECRET."
                ),
            )

    # ── Leg 1: connect ───────────────────────────────────────────────────────

    async def create_authorize_url(self, user_id: UUID) -> str:
        """
        Stage a ticket binding this connect attempt to `user_id`, and return
        the Google authorization URL the browser should be sent to.
        """
        self._require_configured()

        ticket_id = secrets.token_urlsafe(32)
        await self.redis.set(
            f"{_TICKET_KEY_PREFIX}{ticket_id}",
            str(user_id),
            ex=_settings.GOOGLE_DRIVE_TICKET_TTL_SECONDS,
        )

        params = {
            "client_id": _settings.GOOGLE_CLIENT_ID,
            "redirect_uri": _settings.GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(_settings.GOOGLE_DRIVE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": ticket_id,
        }
        return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"

    # ── Leg 2: callback ──────────────────────────────────────────────────────

    async def handle_callback(
        self,
        code: str | None,
        state: str | None,
        google_error: str | None,
    ) -> str:
        """
        Handle Google's redirect back to the backend.

        Always returns a URL to redirect the *browser* to next (either the
        settings page with a claimable exchange code, or with an error
        flag) — this method never raises HTTPException, since the caller
        is a browser navigation, not an API client that can read JSON
        error bodies.
        """
        try:
            if google_error:
                logger.warning("Google Drive OAuth denied or errored", error=google_error)
                raise GoogleDriveOAuthError(google_error)

            if not code or not state:
                raise GoogleDriveOAuthError("missing_code_or_state")

            user_id = await self.redis.get(f"{_TICKET_KEY_PREFIX}{state}")
            if not user_id:
                raise GoogleDriveOAuthError("invalid_or_expired_ticket")
            await self.redis.delete(f"{_TICKET_KEY_PREFIX}{state}")

            tokens = await self._exchange_code_with_google(code)

            exchange_code = secrets.token_urlsafe(32)
            payload = {
                "user_id": user_id,
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token"),
                "scope": tokens.get("scope", " ".join(_settings.GOOGLE_DRIVE_SCOPES)),
                "expires_at": (
                    datetime.now(UTC) + timedelta(seconds=int(tokens["expires_in"]))
                ).isoformat(),
            }
            await self.redis.set(
                f"{_EXCHANGE_KEY_PREFIX}{exchange_code}",
                json.dumps(payload),
                ex=_settings.GOOGLE_DRIVE_EXCHANGE_TTL_SECONDS,
            )

            return self._frontend_redirect(gdrive_exchange=exchange_code)

        except GoogleDriveOAuthError as exc:
            return self._frontend_redirect(gdrive_error=exc.error_code)

    async def _exchange_code_with_google(self, code: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _GOOGLE_TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": _settings.GOOGLE_CLIENT_ID,
                        "client_secret": _settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": _settings.GOOGLE_OAUTH_REDIRECT_URI,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Google token exchange failed",
                status=exc.response.status_code,
                body=exc.response.text[:500],
            )
            raise GoogleDriveOAuthError("token_exchange_failed") from exc
        except httpx.TimeoutException as exc:
            logger.error("Google token exchange timed out")
            raise GoogleDriveOAuthError("token_exchange_timeout") from exc

        data: dict[str, Any] = response.json()
        if "access_token" not in data or "expires_in" not in data:
            raise GoogleDriveOAuthError("malformed_token_response")
        return data

    @staticmethod
    def _frontend_redirect(
        *,
        gdrive_exchange: str | None = None,
        gdrive_error: str | None = None,
    ) -> str:
        params = {"tab": "storage"}
        if gdrive_exchange:
            params["gdrive_exchange"] = gdrive_exchange
        if gdrive_error:
            params["gdrive_error"] = gdrive_error
        return f"{_settings.FRONTEND_URL}/settings?{urlencode(params)}"

    # ── Leg 3: exchange ──────────────────────────────────────────────────────

    async def claim_exchange(self, user_id: UUID, exchange_code: str) -> GoogleDriveTokenResponse:
        """
        Claim a staged exchange code and return the tokens once, deleting
        the code immediately (single use).
        """
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

        return GoogleDriveTokenResponse(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            scope=payload["scope"],
        )

    # ── Leg 4: refresh ───────────────────────────────────────────────────────

    async def refresh_access_token(self, refresh_token: str) -> GoogleDriveTokenResponse:
        """Exchange a refresh token for a new short-lived access token."""
        self._require_configured()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _GOOGLE_TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": _settings.GOOGLE_CLIENT_ID,
                        "client_secret": _settings.GOOGLE_CLIENT_SECRET,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Google token refresh failed",
                status=exc.response.status_code,
                body=exc.response.text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not refresh Google Drive access. Please reconnect.",
            ) from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Google Drive refresh timed out. Please try again.",
            ) from exc

        data = response.json()
        return GoogleDriveTokenResponse(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),  # Google rotates this only sometimes
            expires_at=datetime.now(UTC) + timedelta(seconds=int(data["expires_in"])),
            scope=data.get("scope", " ".join(_settings.GOOGLE_DRIVE_SCOPES)),
        )

    # ── Disconnect ───────────────────────────────────────────────────────────

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke an access or refresh token at Google. Treated as idempotent:
        a token Google already considers invalid still counts as revoked.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _GOOGLE_REVOKE_URL,
                    data={"token": token},
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Google Drive disconnect timed out. Please try again.",
            ) from exc

        if response.status_code in (200, 400):
            # 400 typically means "already invalid" — functionally revoked.
            return True

        logger.error(
            "Google token revoke failed",
            status=response.status_code,
            body=response.text[:500],
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not disconnect Google Drive. Please try again.",
        )
