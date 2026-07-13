"""Response schemas for the stateless (no-persistence) API."""

from __future__ import annotations

from pydantic import BaseModel

from src.schemas.responses.assessment import DimensionScoreSchema, QuestionSchema


class StatelessQuestionsResponse(BaseModel):
    questions: list[QuestionSchema]
    total_questions: int


class StatelessScoreResponse(BaseModel):
    model_version: str
    dimension_scores: list[DimensionScoreSchema]
