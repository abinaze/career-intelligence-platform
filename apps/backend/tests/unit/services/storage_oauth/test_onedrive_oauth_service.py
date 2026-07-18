"""
Unit tests for OneDriveOAuthService.

Same approach as test_google_oauth_service.py: FakeRedis, mocked httpx.
No disconnect tests here — see onedrive_oauth_service.py's module
docstring for why there's no disconnect leg to test.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from fastapi import HTTPException
import httpx
import pytest

from src.core.config.settings import get_settings
from src.services.storage_oauth.onedrive_oauth_service import OneDriveOAuthService
from tests.unit.services.storage_oauth.fakes import FakeRedis

pytestmark = pytest.mark.asyncio

_settings = get_settings()


def _mock_async_client(mocker, *, post_return=None, post_side_effect=None):  # type: ignore[no-untyped-def]
    """Patch httpx.AsyncClient so the service's `async with ... as c: c.post(...)` is mocked."""
    client = MagicMock()
    client.post = AsyncMock(return_value=post_return, side_effect=post_side_effect)

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=client)
    ctx.__aexit__ = AsyncMock(return_value=False)

    mocker.patch(
        "src.services.storage_oauth.onedrive_oauth_service.httpx.AsyncClient",
        return_value=ctx,
    )
    return client


def _microsoft_token_response(
    *,
    access_token: str = "fake-access-token",
    refresh_token: str | None = "fake-refresh-token",
    expires_in: int = 3600,
    scope: str = "Files.ReadWrite.AppFolder offline_access",
) -> httpx.Response:
    body: dict[str, object] = {
        "access_token": access_token,
        "expires_in": expires_in,
        "scope": scope,
    }
    if refresh_token is not None:
        body["refresh_token"] = refresh_token
    return httpx.Response(
        status_code=200,
        json=body,
        request=httpx.Request("POST", "https://login.microsoftonline.com/common/oauth2/v2.0/token"),
    )


@pytest.fixture(autouse=True)
def _configure_microsoft_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_settings, "MICROSOFT_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(_settings, "MICROSOFT_CLIENT_SECRET", "test-client-secret")


class TestCreateAuthorizeUrl:
    async def test_returns_url_and_stages_ticket(self, fake_redis: FakeRedis) -> None:
        service = OneDriveOAuthService(fake_redis)
        user_id = uuid4()

        url = await service.create_authorize_url(user_id)

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        assert parsed.netloc == "login.microsoftonline.com"
        assert "/common/oauth2/v2.0/authorize" in parsed.path
        assert qs["client_id"] == ["test-client-id"]
        assert qs["response_type"] == ["code"]

        ticket_id = qs["state"][0]
        stored_user_id = await fake_redis.get(f"onedrive:ticket:{ticket_id}")
        assert stored_user_id == str(user_id)

    async def test_raises_503_when_not_configured(
        self, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(_settings, "MICROSOFT_CLIENT_ID", None)
        service = OneDriveOAuthService(fake_redis)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_authorize_url(uuid4())
        assert exc_info.value.status_code == 503


class TestHandleCallback:
    async def test_success_stages_exchange_and_deletes_ticket(
        self, fake_redis: FakeRedis, mocker
    ) -> None:
        service = OneDriveOAuthService(fake_redis)
        user_id = uuid4()
        ticket_id = "ticket-abc"
        await fake_redis.set(f"onedrive:ticket:{ticket_id}", str(user_id), ex=300)
        _mock_async_client(mocker, post_return=_microsoft_token_response())

        redirect_url = await service.handle_callback(
            code="auth-code", state=ticket_id, microsoft_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert redirect_url.startswith(_settings.FRONTEND_URL)
        assert "onedrive_exchange" in qs
        assert await fake_redis.get(f"onedrive:ticket:{ticket_id}") is None

    async def test_microsoft_denied_redirects_with_error(self, fake_redis: FakeRedis) -> None:
        service = OneDriveOAuthService(fake_redis)

        redirect_url = await service.handle_callback(
            code=None, state=None, microsoft_error="access_denied"
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["onedrive_error"] == ["access_denied"]

    async def test_missing_code_or_state_redirects_with_error(self, fake_redis: FakeRedis) -> None:
        service = OneDriveOAuthService(fake_redis)

        redirect_url = await service.handle_callback(code="x", state=None, microsoft_error=None)

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["onedrive_error"] == ["missing_code_or_state"]

    async def test_invalid_or_expired_ticket_redirects_with_error(
        self, fake_redis: FakeRedis
    ) -> None:
        service = OneDriveOAuthService(fake_redis)

        redirect_url = await service.handle_callback(
            code="auth-code", state="nonexistent-ticket", microsoft_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["onedrive_error"] == ["invalid_or_expired_ticket"]

    async def test_microsoft_token_exchange_http_error_redirects_with_error(
        self, fake_redis: FakeRedis, mocker
    ) -> None:
        service = OneDriveOAuthService(fake_redis)
        ticket_id = "ticket-err"
        await fake_redis.set(f"onedrive:ticket:{ticket_id}", str(uuid4()), ex=300)
        error_response = httpx.Response(
            status_code=400,
            text="invalid_grant",
            request=httpx.Request(
                "POST", "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            ),
        )
        _mock_async_client(mocker, post_return=error_response)

        redirect_url = await service.handle_callback(
            code="bad-code", state=ticket_id, microsoft_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["onedrive_error"] == ["token_exchange_failed"]

    async def test_microsoft_timeout_redirects_with_error(
        self, fake_redis: FakeRedis, mocker
    ) -> None:
        service = OneDriveOAuthService(fake_redis)
        ticket_id = "ticket-timeout"
        await fake_redis.set(f"onedrive:ticket:{ticket_id}", str(uuid4()), ex=300)
        _mock_async_client(mocker, post_side_effect=httpx.TimeoutException("timed out"))

        redirect_url = await service.handle_callback(
            code="auth-code", state=ticket_id, microsoft_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["onedrive_error"] == ["token_exchange_timeout"]

    async def test_malformed_microsoft_response_redirects_with_error(
        self, fake_redis: FakeRedis, mocker
    ) -> None:
        service = OneDriveOAuthService(fake_redis)
        ticket_id = "ticket-malformed"
        await fake_redis.set(f"onedrive:ticket:{ticket_id}", str(uuid4()), ex=300)
        malformed = httpx.Response(
            status_code=200,
            json={"token_type": "Bearer"},
            request=httpx.Request(
                "POST", "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            ),
        )
        _mock_async_client(mocker, post_return=malformed)

        redirect_url = await service.handle_callback(
            code="auth-code", state=ticket_id, microsoft_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["onedrive_error"] == ["malformed_token_response"]


class TestClaimExchange:
    async def test_success_returns_tokens_and_is_single_use(self, fake_redis: FakeRedis) -> None:
        service = OneDriveOAuthService(fake_redis)
        user_id = uuid4()
        exchange_code = "exchange-abc"
        await fake_redis.set(
            f"onedrive:exchange:{exchange_code}",
            json.dumps(
                {
                    "user_id": str(user_id),
                    "access_token": "tok",
                    "refresh_token": "ref",
                    "scope": "Files.ReadWrite.AppFolder",
                    "expires_at": datetime.now(UTC).isoformat(),
                }
            ),
            ex=60,
        )

        result = await service.claim_exchange(user_id, exchange_code)

        assert result.access_token == "tok"
        assert result.refresh_token == "ref"

        with pytest.raises(HTTPException) as exc_info:
            await service.claim_exchange(user_id, exchange_code)
        assert exc_info.value.status_code == 400

    async def test_invalid_or_expired_code_raises_400(self, fake_redis: FakeRedis) -> None:
        service = OneDriveOAuthService(fake_redis)

        with pytest.raises(HTTPException) as exc_info:
            await service.claim_exchange(uuid4(), "nonexistent")
        assert exc_info.value.status_code == 400

    async def test_wrong_user_raises_403(self, fake_redis: FakeRedis) -> None:
        service = OneDriveOAuthService(fake_redis)
        owner_id = uuid4()
        exchange_code = "exchange-owned"
        await fake_redis.set(
            f"onedrive:exchange:{exchange_code}",
            json.dumps(
                {
                    "user_id": str(owner_id),
                    "access_token": "tok",
                    "refresh_token": "ref",
                    "scope": "Files.ReadWrite.AppFolder",
                    "expires_at": datetime.now(UTC).isoformat(),
                }
            ),
            ex=60,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.claim_exchange(uuid4(), exchange_code)
        assert exc_info.value.status_code == 403


class TestRefreshAccessToken:
    async def test_success_returns_new_access_token(self, fake_redis: FakeRedis, mocker) -> None:
        service = OneDriveOAuthService(fake_redis)
        _mock_async_client(
            mocker,
            post_return=_microsoft_token_response(
                access_token="new-token", refresh_token="new-ref"
            ),
        )

        result = await service.refresh_access_token("some-refresh-token")

        assert result.access_token == "new-token"
        assert result.refresh_token == "new-ref"

    async def test_raises_503_when_not_configured(
        self, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(_settings, "MICROSOFT_CLIENT_SECRET", None)
        service = OneDriveOAuthService(fake_redis)

        with pytest.raises(HTTPException) as exc_info:
            await service.refresh_access_token("some-refresh-token")
        assert exc_info.value.status_code == 503

    async def test_microsoft_error_raises_502(self, fake_redis: FakeRedis, mocker) -> None:
        service = OneDriveOAuthService(fake_redis)
        error_response = httpx.Response(
            status_code=400,
            text="invalid_grant",
            request=httpx.Request(
                "POST", "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            ),
        )
        _mock_async_client(mocker, post_return=error_response)

        with pytest.raises(HTTPException) as exc_info:
            await service.refresh_access_token("bad-refresh-token")
        assert exc_info.value.status_code == 502

    async def test_timeout_raises_504(self, fake_redis: FakeRedis, mocker) -> None:
        service = OneDriveOAuthService(fake_redis)
        _mock_async_client(mocker, post_side_effect=httpx.TimeoutException("timed out"))

        with pytest.raises(HTTPException) as exc_info:
            await service.refresh_access_token("some-refresh-token")
        assert exc_info.value.status_code == 504
