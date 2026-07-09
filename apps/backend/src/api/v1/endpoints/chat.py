"""Career guidance chat API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_current_user
from src.db.engine import get_db
from src.db.models.user import User
from src.schemas.requests.chat import ChatRequest
from src.schemas.responses.chat import ChatResponse
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
        "profile. Pass conversation history to maintain context across turns."
    ),
)
async def send_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.send_message(current_user.id, payload)
