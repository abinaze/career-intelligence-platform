"""Response schemas for the career chat endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    reply: str
    model: str
    tokens_used: int | None = None
    provider_used: Literal["platform", "user_key"] = Field(
        default="platform",
        description=(
            "Which key actually served this reply — 'user_key' when the "
            "request carried an X-User-Anthropic-Key header that was "
            "used, 'platform' otherwise. Shown in the frontend so the "
            "'what goes online' privacy principle "
            "(docs/desktop/TRANSFORMATION_PLAN.md section 2) is true in "
            "the web app too, not just planned for desktop."
        ),
    )


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
