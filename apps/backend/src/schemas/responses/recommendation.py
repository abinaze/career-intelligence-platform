"""Response schemas for the recommendation and careers API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FactorExplanationSchema(BaseModel):
    factor: str
    label: str
    score: float
    driver: str
    detail: str


class CareerExplanationSchema(BaseModel):
    career_id: str
    onet_code: str
    title: str
    summary: str
    confidence_band: str
    factors: list[FactorExplanationSchema]
    top_matching_traits: list[str]


class CareerRecommendationSchema(BaseModel):
    career_id: str
    onet_code: str
    title: str
    broad_category: str
    description: str
    median_salary_usd: float | None = None
    outlook_percentile: float | None = None
    composite_score: float
    similarity_score: float
    riasec_score: float
    explanation: CareerExplanationSchema


class RecommendationResultSchema(BaseModel):
    user_id: str
    profile_completeness: float
    recommendations: list[CareerRecommendationSchema]
    warning: str | None = None


class ProfileSchema(BaseModel):
    """Public profile fields returned by GET /profile."""

    id: str
    user_id: str
    age_range: str | None = None
    education_level: str | None = None
    current_field: str | None = None
    years_of_experience: int | None = None
    country: str | None = None
    primary_goal: str | None = None
    career_concerns: list[str] | None = None
    desired_work_environment: str | None = None
    onboarding_completed: bool
    onboarding_step: int
    completeness_score: float


class ProfileUpdateSchema(BaseModel):
    """PATCH /profile request body — all fields optional."""

    age_range: str | None = Field(default=None, max_length=20)
    education_level: str | None = Field(default=None, max_length=100)
    current_field: str | None = Field(default=None, max_length=200)
    years_of_experience: int | None = Field(default=None, ge=0, le=60)
    country: str | None = Field(default=None, max_length=100)
    primary_goal: str | None = Field(default=None, max_length=500)
    career_concerns: list[str] | None = None
    desired_work_environment: str | None = Field(default=None, max_length=200)
    onboarding_step: int | None = Field(default=None, ge=0)
    onboarding_completed: bool | None = None
