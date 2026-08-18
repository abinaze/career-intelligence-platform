"""Request schemas for the career chat endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a conversation turn."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    """Request body for POST /chat/message."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's latest message.",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
        description="Previous conversation turns (oldest first, max 20).",
    )


class TestConnectionRequest(BaseModel):
    """Request body for POST /chat/test-connection."""

    api_key: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description=(
            "The Anthropic API key to validate. Used for exactly one "
            "minimal test call and never persisted on the backend."
        ),
    )
