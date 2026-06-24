"""Request schemas for the assessment API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StartAssessmentRequest(BaseModel):
    """Request body to begin a new assessment session."""

    assessment_type: str = Field(
        default="full",
        description="Assessment type: 'full' (all dimensions) or 'quick' (OCEAN only).",
    )


class SubmitAssessmentRequest(BaseModel):
    """Submit responses for a completed assessment session."""

    session_id: str = Field(description="UUID of the active assessment session.")
    responses: dict[str, int] = Field(description="Map of question_id -> Likert response (1-5).")
