"""
Career guidance chat service.

Uses the Anthropic Claude API to provide contextual career advice.
The system prompt is dynamically built from the user's psychometric
scores and profile so every answer is personalised.

The service is stateless — conversation history is passed in by
the client and stored in frontend Zustand state only.
"""

from __future__ import annotations

import uuid

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.settings import get_settings
from src.core.logging.setup import get_logger
from src.db.models.profile import UserProfile
from src.db.repositories.psychometric import PsychometricScoreRepository
from src.schemas.requests.chat import ChatMessage, ChatRequest, ChatResponse

logger = get_logger(__name__)
_settings = get_settings()

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 1024


def _build_system_prompt(
    score_map: dict[str, float],
    profile_meta: dict[str, str | None],
) -> str:
    """
    Build a personalised system prompt from the user's psychometric profile.
    """
    lines: list[str] = [
        "You are a professional career guidance counsellor with deep expertise in "
        "psychometrics, occupational psychology, and career development.",
        "",
        "You are speaking with a user whose career profile is summarised below. "
        "Use this context to make every answer specific and actionable — "
        "never give generic advice.",
        "",
        "## User profile",
    ]

    if education := profile_meta.get("education_level"):
        lines.append(f"- Education: {education}")
    if field := profile_meta.get("current_field"):
        lines.append(f"- Current field: {field}")
    if goal := profile_meta.get("primary_goal"):
        lines.append(f"- Career goal: {goal}")
    if env := profile_meta.get("desired_work_environment"):
        lines.append(f"- Preferred environment: {env}")

    if score_map:
        lines.append("")
        lines.append("## Psychometric scores (0–100)")
        top = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
        for dim, score in top:
            lines.append(f"- {dim.replace('_', ' ').title()}: {score:.0f}/100")

    lines += [
        "",
        "## Instructions",
        "- Be concise, warm, and evidence-based.",
        "- Reference the user's specific scores and goals when relevant.",
        "- If asked about career options, relate them to the user's top dimensions.",
        "- Do not hallucinate job titles or salary figures — say you don't know if uncertain.",
        "- Never break character or discuss your underlying model.",
        "- Respond in plain prose, no markdown headers.",
        "- Keep responses under 250 words unless asked for detail.",
    ]
    return "\n".join(lines)


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.score_repo = PsychometricScoreRepository(db)

    async def send_message(
        self,
        user_id: uuid.UUID,
        payload: ChatRequest,
    ) -> ChatResponse:
        """
        Send a chat message and return an AI reply.

        Loads the user's profile and psychometric scores to build a
        personalised system prompt, then calls the Anthropic API.
        """
        # Load profile
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        score_map: dict[str, float] = {}
        profile_meta: dict[str, str | None] = {}

        if profile:
            profile_meta = {
                "education_level": profile.education_level,
                "current_field": profile.current_field,
                "primary_goal": profile.primary_goal,
                "desired_work_environment": profile.desired_work_environment,
            }
            scores = await self.score_repo.get_latest_for_profile(profile.id)
            score_map = {s.dimension: s.score for s in scores}

        system_prompt = _build_system_prompt(score_map, profile_meta)

        # Build message list for Anthropic API
        messages: list[dict[str, str]] = [
            {"role": m.role, "content": m.content}
            for m in payload.history[-18:]  # keep last 18 turns + new message
        ]
        messages.append({"role": "user", "content": payload.message})

        api_key = getattr(_settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chat service is not configured. Set ANTHROPIC_API_KEY.",
            )

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
                        "max_tokens": _MAX_TOKENS,
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
            )
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

        logger.info(
            "Chat message processed",
            user_id=str(user_id),
            tokens=tokens_used,
        )

        return ChatResponse(
            reply=reply_text,
            model=_MODEL,
            tokens_used=tokens_used,
        )
