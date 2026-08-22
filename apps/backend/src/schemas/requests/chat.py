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
    score_map: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "The user's own psychometric dimension scores (0-100), supplied "
            "by the client so the system prompt can be personalised. There is "
            "no account system in this product (see docs/NORTH_STAR.md) — the "
            "client already holds this data locally from the stateless "
            "assessment flow and passes it along here rather than the "
            "backend looking it up by a user id that no longer exists."
        ),
    )
    profile_meta: dict[str, str | None] = Field(
        default_factory=dict,
        description=(
            "Optional biographical fields (education_level, current_field, "
            "primary_goal, desired_work_environment) for the same reason as "
            "score_map — supplied by the client, not looked up server-side."
        ),
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
