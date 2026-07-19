"""
Unit tests for DropboxOAuthService. Same approach as
test_google_oauth_service.py — FakeRedis, mocked httpx. Includes
disconnect tests (unlike OneDrive's suite), since Dropbox has a real
revoke endpoint.
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
from src.services.storage_oauth.dropbox_oauth_service import DropboxOAuthService
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
        "src.services.storage_oauth.dropbox_oauth_service.httpx.AsyncClient",
        return_value=ctx,
    )
    return client


def _dropbox_token_response(
    *,
    access_token: str = "fake-access-token",
    refresh_token: str | None = "fake-refresh-token",
    expires_in: int = 14400,
    scope: str = "files.content.write files.content.read",
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
        request=httpx.Request("POST", "https://api.dropboxapi.com/oauth2/token"),
    )


@pytest.fixture(autouse=True)
def _configure_dropbox_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_settings, "DROPBOX_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(_settings, "DROPBOX_CLIENT_SECRET", "test-client-secret")


class TestCreateAuthorizeUrl:
    async def test_returns_url_and_stages_ticket(self, fake_redis: FakeRedis) -> None:
        service = DropboxOAuthService(fake_redis)
        user_id = uuid4()

        url = await service.create_authorize_url(user_id)

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        assert parsed.netloc == "www.dropbox.com"
        assert qs["client_id"] == ["test-client-id"]
        assert qs["token_access_type"] == ["offline"]

        ticket_id = qs["state"][0]
        stored_user_id = await fake_redis.get(f"dropbox:ticket:{ticket_id}")
        assert stored_user_id == str(user_id)

    async def test_raises_503_when_not_configured(
        self, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(_settings, "DROPBOX_CLIENT_ID", None)
        service = DropboxOAuthService(fake_redis)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_authorize_url(uuid4())
        assert exc_info.value.status_code == 503


class TestHandleCallback:
    async def test_success_stages_exchange_and_deletes_ticket(
        self, fake_redis: FakeRedis, mocker
    ) -> None:
        service = DropboxOAuthService(fake_redis)
        user_id = uuid4()
        ticket_id = "ticket-abc"
        await fake_redis.set(f"dropbox:ticket:{ticket_id}", str(user_id), ex=300)
        _mock_async_client(mocker, post_return=_dropbox_token_response())

        redirect_url = await service.handle_callback(
            code="auth-code", state=ticket_id, dropbox_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert redirect_url.startswith(_settings.FRONTEND_URL)
        assert "dropbox_exchange" in qs
        assert await fake_redis.get(f"dropbox:ticket:{ticket_id}") is None

    async def test_dropbox_denied_redirects_with_error(self, fake_redis: FakeRedis) -> None:
        service = DropboxOAuthService(fake_redis)

        redirect_url = await service.handle_callback(
            code=None, state=None, dropbox_error="access_denied"
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["dropbox_error"] == ["access_denied"]

    async def test_missing_code_or_state_redirects_with_error(self, fake_redis: FakeRedis) -> None:
        service = DropboxOAuthService(fake_redis)

        redirect_url = await service.handle_callback(code="x", state=None, dropbox_error=None)

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["dropbox_error"] == ["missing_code_or_state"]

    async def test_invalid_or_expired_ticket_redirects_with_error(
        self, fake_redis: FakeRedis
    ) -> None:
        service = DropboxOAuthService(fake_redis)

        redirect_url = await service.handle_callback(
            code="auth-code", state="nonexistent-ticket", dropbox_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["dropbox_error"] == ["invalid_or_expired_ticket"]

    async def test_dropbox_token_exchange_http_error_redirects_with_error(
        self, fake_redis: FakeRedis, mocker
    ) -> None:
        service = DropboxOAuthService(fake_redis)
        ticket_id = "ticket-err"
        await fake_redis.set(f"dropbox:ticket:{ticket_id}", str(uuid4()), ex=300)
        error_response = httpx.Response(
            status_code=400,
            text="invalid_grant",
            request=httpx.Request("POST", "https://api.dropboxapi.com/oauth2/token"),
        )
        _mock_async_client(mocker, post_return=error_response)

        redirect_url = await service.handle_callback(
            code="bad-code", state=ticket_id, dropbox_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["dropbox_error"] == ["token_exchange_failed"]

    async def test_dropbox_timeout_redirects_with_error(
        self, fake_redis: FakeRedis, mocker
    ) -> None:
        service = DropboxOAuthService(fake_redis)
        ticket_id = "ticket-timeout"
        await fake_redis.set(f"dropbox:ticket:{ticket_id}", str(uuid4()), ex=300)
        _mock_async_client(mocker, post_side_effect=httpx.TimeoutException("timed out"))

        redirect_url = await service.handle_callback(
            code="auth-code", state=ticket_id, dropbox_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["dropbox_error"] == ["token_exchange_timeout"]

    async def test_malformed_dropbox_response_redirects_with_error(
        self, fake_redis: FakeRedis, mocker
    ) -> None:
        service = DropboxOAuthService(fake_redis)
        ticket_id = "ticket-malformed"
        await fake_redis.set(f"dropbox:ticket:{ticket_id}", str(uuid4()), ex=300)
        malformed = httpx.Response(
            status_code=200,
            json={"token_type": "bearer"},
            request=httpx.Request("POST", "https://api.dropboxapi.com/oauth2/token"),
        )
        _mock_async_client(mocker, post_return=malformed)

        redirect_url = await service.handle_callback(
            code="auth-code", state=ticket_id, dropbox_error=None
        )

        qs = parse_qs(urlparse(redirect_url).query)
        assert qs["dropbox_error"] == ["malformed_token_response"]


class TestClaimExchange:
    async def test_success_returns_tokens_and_is_single_use(self, fake_redis: FakeRedis) -> None:
        service = DropboxOAuthService(fake_redis)
        user_id = uuid4()
        exchange_code = "exchange-abc"
        await fake_redis.set(
            f"dropbox:exchange:{exchange_code}",
            json.dumps(
                {
                    "user_id": str(user_id),
                    "access_token": "tok",
                    "refresh_token": "ref",
                    "scope": "files.content.write",
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
        service = DropboxOAuthService(fake_redis)

        with pytest.raises(HTTPException) as exc_info:
            await service.claim_exchange(uuid4(), "nonexistent")
        assert exc_info.value.status_code == 400

    async def test_wrong_user_raises_403(self, fake_redis: FakeRedis) -> None:
        service = DropboxOAuthService(fake_redis)
        owner_id = uuid4()
        exchange_code = "exchange-owned"
        await fake_redis.set(
            f"dropbox:exchange:{exchange_code}",
            json.dumps(
                {
                    "user_id": str(owner_id),
                    "access_token": "tok",
                    "refresh_token": "ref",
                    "scope": "files.content.write",
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
        service = DropboxOAuthService(fake_redis)
        _mock_async_client(mocker, post_return=_dropbox_token_response(access_token="new-token"))

        result = await service.refresh_access_token("some-refresh-token")

        assert result.access_token == "new-token"

    async def test_raises_503_when_not_configured(
        self, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(_settings, "DROPBOX_CLIENT_SECRET", None)
        service = DropboxOAuthService(fake_redis)

        with pytest.raises(HTTPException) as exc_info:
            await service.refresh_access_token("some-refresh-token")
        assert exc_info.value.status_code == 503

    async def test_dropbox_error_raises_502(self, fake_redis: FakeRedis, mocker) -> None:
        service = DropboxOAuthService(fake_redis)
        error_response = httpx.Response(
            status_code=400,
            text="invalid_grant",
            request=httpx.Request("POST", "https://api.dropboxapi.com/oauth2/token"),
        )
        _mock_async_client(mocker, post_return=error_response)

        with pytest.raises(HTTPException) as exc_info:
            await service.refresh_access_token("bad-refresh-token")
        assert exc_info.value.status_code == 502

    async def test_timeout_raises_504(self, fake_redis: FakeRedis, mocker) -> None:
        service = DropboxOAuthService(fake_redis)
        _mock_async_client(mocker, post_side_effect=httpx.TimeoutException("timed out"))

        with pytest.raises(HTTPException) as exc_info:
            await service.refresh_access_token("some-refresh-token")
        assert exc_info.value.status_code == 504


class TestRevokeToken:
    async def test_200_counts_as_revoked(self, fake_redis: FakeRedis, mocker) -> None:
        service = DropboxOAuthService(fake_redis)
        ok_response = httpx.Response(
            status_code=200,
            request=httpx.Request("POST", "https://api.dropboxapi.com/2/auth/token/revoke"),
        )
        _mock_async_client(mocker, post_return=ok_response)

        assert await service.revoke_token("some-token") is True

    async def test_401_still_counts_as_revoked(self, fake_redis: FakeRedis, mocker) -> None:
        service = DropboxOAuthService(fake_redis)
        already_invalid = httpx.Response(
            status_code=401,
            request=httpx.Request("POST", "https://api.dropboxapi.com/2/auth/token/revoke"),
        )
        _mock_async_client(mocker, post_return=already_invalid)

        assert await service.revoke_token("some-token") is True

    async def test_server_error_raises_502(self, fake_redis: FakeRedis, mocker) -> None:
        service = DropboxOAuthService(fake_redis)
        server_error = httpx.Response(
            status_code=500,
            request=httpx.Request("POST", "https://api.dropboxapi.com/2/auth/token/revoke"),
        )
        _mock_async_client(mocker, post_return=server_error)

        with pytest.raises(HTTPException) as exc_info:
            await service.revoke_token("some-token")
        assert exc_info.value.status_code == 502

    async def test_timeout_raises_504(self, fake_redis: FakeRedis, mocker) -> None:
        service = DropboxOAuthService(fake_redis)
        _mock_async_client(mocker, post_side_effect=httpx.TimeoutException("timed out"))

        with pytest.raises(HTTPException) as exc_info:
            await service.revoke_token("some-token")
        assert exc_info.value.status_code == 504
