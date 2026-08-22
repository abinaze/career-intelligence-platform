"""Career guidance chat API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Header, status

from src.schemas.requests.chat import ChatRequest, TestConnectionRequest
from src.schemas.responses.chat import ChatResponse, TestConnectionResponse
from src.services.chat.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_service() -> ChatService:
    return ChatService()


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a career guidance chat message",
    description=(
        "Send a message to the AI career counsellor. The system prompt is "
        "personalised from the score_map/profile_meta the client supplies "
        "directly in the request body (there is no account system in this "
        "product — see docs/NORTH_STAR.md). Pass conversation history to "
        "maintain context across turns. Optionally supply an "
        "X-User-Anthropic-Key header to use your own Anthropic API key "
        "instead of the platform's — it's used for this request only and "
        "never stored on the backend."
    ),
)
async def send_message(
    payload: ChatRequest,
    x_user_anthropic_key: str | None = Header(default=None, alias="X-User-Anthropic-Key"),
) -> ChatResponse:
    return await get_chat_service().send_message(payload, user_api_key=x_user_anthropic_key)


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
) -> TestConnectionResponse:
    success, message = await get_chat_service().test_connection(payload.api_key)
    return TestConnectionResponse(success=success, message=message)
