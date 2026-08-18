"""
Unit tests for the LLM provider abstraction (llm_provider.py).

Mocks all outbound httpx calls to Anthropic, so these run with no
network access. Follows the same mocking convention as
tests/unit/services/storage_oauth/test_google_oauth_service.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
import httpx
import pytest

from src.services.chat.llm_provider import (
    PlatformAnthropicProvider,
    UserSuppliedKeyProvider,
    resolve_llm_provider,
    verify_anthropic_key,
)

pytestmark = pytest.mark.asyncio


def _mock_async_client(mocker, *, post_return=None, post_side_effect=None):  # type: ignore[no-untyped-def]
    """Patch httpx.AsyncClient so the module's `async with ... as c: c.post(...)` is mocked."""
    client = MagicMock()
    client.post = AsyncMock(return_value=post_return, side_effect=post_side_effect)

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=client)
    ctx.__aexit__ = AsyncMock(return_value=False)

    mocker.patch(
        "src.services.chat.llm_provider.httpx.AsyncClient",
        return_value=ctx,
    )
    return client


def _anthropic_success_response(text: str = "Hello!", output_tokens: int = 12):  # type: ignore[no-untyped-def]
    response = MagicMock(spec=httpx.Response)
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "content": [{"type": "text", "text": text}],
        "usage": {"output_tokens": output_tokens},
    }
    return response


def _anthropic_error_response(status_code: int, body: str = "unauthorized"):  # type: ignore[no-untyped-def]
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code, request=request, text=body)

    def _raise() -> None:
        raise httpx.HTTPStatusError(body, request=request, response=response)

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status.side_effect = _raise
    mock_response.status_code = status_code
    mock_response.text = body
    return mock_response


class TestResolveLlmProvider:
    async def test_prefers_user_key_when_present(self) -> None:
        provider = resolve_llm_provider(platform_api_key="platform-key", user_api_key="user-key")
        assert isinstance(provider, UserSuppliedKeyProvider)
        assert provider.source == "user_key"

    async def test_falls_back_to_platform_when_no_user_key(self) -> None:
        provider = resolve_llm_provider(platform_api_key="platform-key", user_api_key=None)
        assert isinstance(provider, PlatformAnthropicProvider)
        assert provider.source == "platform"

    async def test_falls_back_to_platform_even_when_platform_key_missing(self) -> None:
        # Resolution itself doesn't fail here — PlatformAnthropicProvider
        # raises its own 503 at call time, not at resolution time.
        provider = resolve_llm_provider(platform_api_key=None, user_api_key=None)
        assert isinstance(provider, PlatformAnthropicProvider)


class TestPlatformAnthropicProvider:
    async def test_raises_503_when_no_platform_key_configured(self) -> None:
        provider = PlatformAnthropicProvider(api_key=None)
        with pytest.raises(HTTPException) as exc_info:
            await provider.complete("system", [{"role": "user", "content": "hi"}])
        assert exc_info.value.status_code == 503

    async def test_completes_successfully_with_platform_key(self, mocker) -> None:  # type: ignore[no-untyped-def]
        client = _mock_async_client(mocker, post_return=_anthropic_success_response("Hi there!"))
        provider = PlatformAnthropicProvider(api_key="sk-platform-key")

        completion = await provider.complete("system prompt", [{"role": "user", "content": "hi"}])

        assert completion.reply == "Hi there!"
        assert completion.provider_used == "platform"
        assert completion.tokens_used == 12
        sent_headers = client.post.call_args.kwargs["headers"]
        assert sent_headers["x-api-key"] == "sk-platform-key"


class TestUserSuppliedKeyProvider:
    async def test_completes_successfully_with_user_key(self, mocker) -> None:  # type: ignore[no-untyped-def]
        client = _mock_async_client(mocker, post_return=_anthropic_success_response("Custom reply"))
        provider = UserSuppliedKeyProvider(api_key="sk-user-own-key")

        completion = await provider.complete("system prompt", [{"role": "user", "content": "hi"}])

        assert completion.reply == "Custom reply"
        assert completion.provider_used == "user_key"
        sent_headers = client.post.call_args.kwargs["headers"]
        assert sent_headers["x-api-key"] == "sk-user-own-key"

    async def test_rejected_key_surfaces_as_422_not_502(self, mocker) -> None:  # type: ignore[no-untyped-def]
        _mock_async_client(mocker, post_return=_anthropic_error_response(401, "invalid x-api-key"))
        provider = UserSuppliedKeyProvider(api_key="sk-bad-key")

        with pytest.raises(HTTPException) as exc_info:
            await provider.complete("system prompt", [{"role": "user", "content": "hi"}])

        # 401/403 from a user-supplied key is a client-fixable problem,
        # not a platform outage — should not be a 502.
        assert exc_info.value.status_code == 422
        # Anthropic's raw error body must never leak into the message
        # shown to the user.
        assert "invalid x-api-key" not in exc_info.value.detail

    async def test_platform_side_error_still_surfaces_as_502(self, mocker) -> None:  # type: ignore[no-untyped-def]
        _mock_async_client(mocker, post_return=_anthropic_error_response(500, "internal error"))
        provider = UserSuppliedKeyProvider(api_key="sk-any-key")

        with pytest.raises(HTTPException) as exc_info:
            await provider.complete("system prompt", [{"role": "user", "content": "hi"}])

        assert exc_info.value.status_code == 502

    async def test_timeout_surfaces_as_504(self, mocker) -> None:  # type: ignore[no-untyped-def]
        _mock_async_client(mocker, post_side_effect=httpx.TimeoutException("timed out"))
        provider = UserSuppliedKeyProvider(api_key="sk-any-key")

        with pytest.raises(HTTPException) as exc_info:
            await provider.complete("system prompt", [{"role": "user", "content": "hi"}])

        assert exc_info.value.status_code == 504

    async def test_never_logs_the_api_key(self, mocker) -> None:  # type: ignore[no-untyped-def]
        """A rejected key's value must never appear in the error log call."""
        _mock_async_client(mocker, post_return=_anthropic_error_response(401, "invalid x-api-key"))
        log_error = mocker.patch("src.services.chat.llm_provider.logger.error")
        provider = UserSuppliedKeyProvider(api_key="sk-super-secret-value")

        with pytest.raises(HTTPException):
            await provider.complete("system prompt", [{"role": "user", "content": "hi"}])

        log_error.assert_called_once()
        logged_kwargs = log_error.call_args.kwargs
        assert "sk-super-secret-value" not in str(log_error.call_args)
        assert logged_kwargs["source"] == "user_key"


class TestVerifyAnthropicKey:
    async def test_returns_success_for_a_working_key(self, mocker) -> None:  # type: ignore[no-untyped-def]
        _mock_async_client(mocker, post_return=_anthropic_success_response("ok"))
        success, _message = await verify_anthropic_key("sk-good-key")
        assert success is True

    async def test_returns_friendly_message_for_a_bad_key(self, mocker) -> None:  # type: ignore[no-untyped-def]
        _mock_async_client(mocker, post_return=_anthropic_error_response(401, "invalid x-api-key"))
        success, message = await verify_anthropic_key("sk-bad-key")
        assert success is False
        assert "invalid x-api-key" not in message
        assert "rejected" in message.lower()

    async def test_never_raises(self, mocker) -> None:  # type: ignore[no-untyped-def]
        _mock_async_client(mocker, post_side_effect=httpx.TimeoutException("timed out"))
        success, _message = await verify_anthropic_key("sk-any-key")
        assert success is False
