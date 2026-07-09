"""Response schemas for the career chat endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class ChatResponse(BaseModel):
    reply: str
    model: str
    tokens_used: int | None = None
