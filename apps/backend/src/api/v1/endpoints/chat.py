"""Career guidance chat API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_current_user
from src.db.engine import get_db
from src.db.models.user import User
from src.schemas.requests.chat import ChatRequest, TestConnectionRequest
from src.schemas.responses.chat import ChatResponse, TestConnectionResponse
from src.services.chat.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


async def get_chat_service(
    db: AsyncSession = Depends(get_db),
) -> ChatService:
    return ChatService(db)


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a career guidance chat message",
    description=(
        "Send a message to the AI career counsellor. The system prompt is "
        "automatically personalised from the user's psychometric scores and "
        "profile. Pass conversation history to maintain context across turns. "
        "Optionally supply an X-User-Anthropic-Key header to use your own "
        "Anthropic API key instead of the platform's — it's used for this "
        "request only and never stored on the backend."
    ),
)
async def send_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
    x_user_anthropic_key: str | None = Header(default=None, alias="X-User-Anthropic-Key"),
) -> ChatResponse:
    return await service.send_message(current_user.id, payload, user_api_key=x_user_anthropic_key)


@router.post(
    "/test-connection",
    response_model=TestConnectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate a user-supplied Anthropic API key",
    description=(
        "Makes one minimal Anthropic API call to check whether a key works, "
        "before the user saves it. The key is used for this single request "
        "only and is never persisted on the backend — the frontend is "
        "responsible for storing it client-side once this confirms it's valid."
    ),
)
async def test_connection(
    payload: TestConnectionRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> TestConnectionResponse:
    success, message = await service.test_connection(payload.api_key)
    return TestConnectionResponse(success=success, message=message)
