"""
LLM provider abstraction for the career guidance chat feature.

Two implementations exist today, both talking to Anthropic's API — this
project has no local-LLM code yet (see
docs/desktop/TRANSFORMATION_PLAN.md section 7: local chat is
intentionally deferred past v1, since there's no existing fallback
pattern to build on the way embeddings and FAISS have). This
abstraction exists now so a future LocalLLMProvider or a different
hosted provider can be added later without touching ChatService's own
logic — the same reason the frontend's StorageAdapter interface exists
for BYOS storage (see docs/architecture/byos.md).

A user-supplied key is never written to the database or any persistent
store on this backend — it lives in memory for the lifetime of a single
request. That's the same trust boundary already applied to the BYOS
OAuth brokers' tokens (see docs/architecture/byos.md's "never persist
tokens" principle). The frontend is responsible for storing it
client-side (IndexedDB, not localStorage — see
features/aiProviders/lib/anthropicKeyStorage.ts) and re-sending it on
every request that should use it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, status
import httpx

from src.core.logging.setup import get_logger

logger = get_logger(__name__)

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-sonnet-4-6"

ProviderSource = Literal["platform", "user_key"]


@dataclass(frozen=True)
class LLMCompletion:
    reply: str
    model: str
    tokens_used: int | None
    provider_used: ProviderSource


class LLMProvider(ABC):
    """A source of chat completions. Implementations own their own API key."""

    source: ProviderSource

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
    ) -> LLMCompletion: ...


async def _call_anthropic(
    api_key: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    source: ProviderSource,
) -> LLMCompletion:
    """
    Shared Anthropic Messages API call used by both providers below.

    Never logs `api_key` — only Anthropic's own response status and a
    truncated error body, matching the redaction discipline already
    used elsewhere in this project for BYO credentials.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": _MODEL,
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": messages,
                },
            )
            response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Anthropic API error",
            status=exc.response.status_code,
            body=exc.response.text[:500],
            source=source,
        )
        if source == "user_key" and exc.response.status_code in (401, 403):
            # A user's own key being rejected is a different situation
            # from the platform's own key failing — surface it as a
            # client-fixable problem (422) rather than a 502, so the
            # frontend can show "check your key" instead of "try again
            # later".
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Your API key was rejected. Check that it's valid and try again.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Chat service temporarily unavailable. Please try again.",
        ) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Chat service timed out. Please try again.",
        ) from exc

    data = response.json()
    reply_text: str = data["content"][0]["text"]
    tokens_used: int | None = data.get("usage", {}).get("output_tokens")
    return LLMCompletion(
        reply=reply_text,
        model=_MODEL,
        tokens_used=tokens_used,
        provider_used=source,
    )


class PlatformAnthropicProvider(LLMProvider):
    """Uses the platform's own ANTHROPIC_API_KEY — the original, default behavior."""

    source: ProviderSource = "platform"

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    async def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
    ) -> LLMCompletion:
        if not self._api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Chat isn't configured with a platform API key. "
                    "Connect your own Anthropic key in Settings to use chat."
                ),
            )
        return await _call_anthropic(
            self._api_key, system_prompt, messages, max_tokens, self.source
        )


class UserSuppliedKeyProvider(LLMProvider):
    """Uses a key the caller supplied for this request only. See module docstring."""

    source: ProviderSource = "user_key"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
    ) -> LLMCompletion:
        return await _call_anthropic(
            self._api_key, system_prompt, messages, max_tokens, self.source
        )


def resolve_llm_provider(
    platform_api_key: str | None,
    user_api_key: str | None,
) -> LLMProvider:
    """
    Picks which provider a request should use.

    A user-supplied key always takes priority when present — someone
    who's gone to the trouble of connecting their own key expects it to
    actually be used, not silently ignored in favor of the platform's.
    """
    if user_api_key:
        return UserSuppliedKeyProvider(user_api_key)
    return PlatformAnthropicProvider(platform_api_key)


async def verify_anthropic_key(api_key: str) -> tuple[bool, str]:
    """
    Makes one minimal Anthropic API call to check whether a key works.

    Returns (success, human_readable_message). Never raises, and never
    surfaces Anthropic's raw error text — matching the "never expose
    raw technical errors" principle used throughout this project's BYOS
    connect flows (see docs/architecture/byos.md).
    """
    try:
        await _call_anthropic(
            api_key,
            system_prompt="Reply with the single word: ok",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=8,
            source="user_key",
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
            return False, "That key was rejected. Check that it's valid and try again."
        return False, "Couldn't reach Anthropic right now. Please try again."
    return True, "Connection successful."
