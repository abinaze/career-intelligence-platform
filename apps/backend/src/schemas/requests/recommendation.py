"""Request schemas for the recommendation API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """Optional parameters for tuning recommendation results."""

    top_k: int = Field(default=10, ge=1, le=50, description="Number of recommendations to return.")
