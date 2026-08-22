"""
Career guidance chat service.

Uses the Anthropic Claude API to provide contextual career advice.
The system prompt is personalised from psychometric scores and profile
data the client supplies directly in the request — since the Cloud
archive (see docs/NORTH_STAR.md) there is no account system and no
per-user database row to load this from server-side, so it travels
with the request the same way conversation history already did.

The service is otherwise unchanged: stateless — conversation history
is passed in by the client and stored in frontend Zustand state only.

A request can optionally supply its own Anthropic API key (see
llm_provider.py) instead of using the platform's.
"""

from __future__ import annotations

from src.core.config.settings import get_settings
from src.core.logging.setup import get_logger
from src.schemas.requests.chat import ChatRequest
from src.schemas.responses.chat import ChatResponse
from src.services.chat.llm_provider import resolve_llm_provider, verify_anthropic_key

logger = get_logger(__name__)
_settings = get_settings()


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
        lines.append("## Psychometric scores (0-100)")
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
    def __init__(self) -> None:
        pass  # no state, no DB — kept as a class to match the shape of
        # the other services in this codebase and leave room for future
        # per-instance state (e.g. a local LLM handle) without another
        # signature change.

    async def send_message(
        self,
        payload: ChatRequest,
        user_api_key: str | None = None,
    ) -> ChatResponse:
        """
        Send a chat message and return an AI reply.

        Builds a personalised system prompt from `payload.score_map`/
        `payload.profile_meta` (supplied by the client — see
        ChatRequest's own docstring for why), then calls whichever LLM
        provider `resolve_llm_provider` picks. If `user_api_key` is
        supplied, it takes priority over the platform's own key — see
        llm_provider.py's module docstring for why it's never persisted
        here.
        """
        system_prompt = _build_system_prompt(payload.score_map, payload.profile_meta)

        # Build message list for the LLM API
        messages: list[dict[str, str]] = [
            {"role": m.role, "content": m.content}
            for m in payload.history[-18:]  # keep last 18 turns + new message
        ]
        messages.append({"role": "user", "content": payload.message})

        provider = resolve_llm_provider(
            platform_api_key=getattr(_settings, "ANTHROPIC_API_KEY", None),
            user_api_key=user_api_key,
        )
        completion = await provider.complete(system_prompt, messages)

        logger.info(
            "Chat message processed",
            tokens=completion.tokens_used,
            provider=completion.provider_used,
        )

        return ChatResponse(
            reply=completion.reply,
            model=completion.model,
            tokens_used=completion.tokens_used,
            provider_used=completion.provider_used,
        )

    async def test_connection(self, api_key: str) -> tuple[bool, str]:
        """
        Validates a user-supplied API key with one minimal Anthropic
        call, without persisting it anywhere. See llm_provider.py's
        verify_anthropic_key for the actual call and its error mapping.
        """
        return await verify_anthropic_key(api_key)
