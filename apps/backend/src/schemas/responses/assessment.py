"""Response schemas for the assessment API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from src.ai.psychometric_engine.dimensions import DimensionMetadata, PsychometricDimension


class QuestionSchema(BaseModel):
    id: str
    dimension: str
    prompt: str
    reverse_scored: bool


class AssessmentSessionSchema(BaseModel):
    session_id: uuid.UUID
    assessment_type: str
    status: str
    started_at: datetime
    questions: list[QuestionSchema]

    model_config = {"from_attributes": True}


class DimensionScoreSchema(BaseModel):
    dimension: PsychometricDimension
    display_name: str
    description: str
    score: float
    confidence: float
    item_count: int
    low_label: str
    high_label: str


class AssessmentResultSchema(BaseModel):
    session_id: uuid.UUID
    model_version: str
    completed_at: datetime
    dimension_scores: list[DimensionScoreSchema]
