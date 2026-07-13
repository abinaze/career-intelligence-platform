"""
Request schemas for the stateless (no-persistence) API.

These endpoints support the local-device and bring-your-own-storage
frontends: the caller supplies data directly in the request body instead
of the backend looking it up from a per-user database record. The
backend performs compute only — it does not read or write personal data
for these requests. Shared, non-personal data (the career catalog, the
FAISS index) is still read from the database, since that data belongs
to the platform, not to any individual user.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StatelessQuestionsRequest(BaseModel):
    """Query parameters for fetching the static question bank."""

    assessment_type: str = Field(
        default="full",
        description="Assessment type: 'full' (all dimensions) or 'quick' (OCEAN only).",
    )


class StatelessScoreRequest(BaseModel):
    """Score a set of Likert responses without persisting anything."""

    responses: dict[str, int] = Field(description="Map of question_id -> Likert response (1-5).")


class StatelessProfileMeta(BaseModel):
    """Optional profile context supplied directly by the caller."""

    education_level: str | None = None
    current_field: str | None = None
    primary_goal: str | None = None
    desired_work_environment: str | None = None
    years_of_experience: int | None = None
    country: str | None = None
    age_range: str | None = None
    career_concerns: list[str] | None = None


class StatelessRecommendationRequest(BaseModel):
    """
    Generate recommendations from client-supplied psychometric scores
    and profile data, rather than looking them up from the database.
    """

    dimension_scores: dict[str, float] = Field(
        description="Map of dimension name -> score (0-100), from a prior scoring call."
    )
    profile: StatelessProfileMeta = Field(default_factory=StatelessProfileMeta)
    top_k: int = Field(default=10, ge=1, le=50)
