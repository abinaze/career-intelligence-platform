"""
Stateless service.

Backs the local-device / bring-your-own-storage frontend flows. Every
method here computes a result from data supplied directly in the
request and returns it — nothing about the caller's profile or
assessment responses is written to the database. Only the shared,
non-personal career catalog and FAISS index are read.

See docs/architecture/byos.md for the full design rationale.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.psychometric_engine.dimensions import DIMENSION_METADATA
from src.ai.psychometric_engine.question_bank import get_questions_for_type
from src.ai.psychometric_engine.scorer import score_responses
from src.core.logging.setup import get_logger
from src.schemas.requests.stateless import (
    StatelessProfileMeta,
    StatelessRecommendationRequest,
    StatelessScoreRequest,
)
from src.schemas.responses.assessment import DimensionScoreSchema, QuestionSchema
from src.schemas.responses.stateless import StatelessQuestionsResponse, StatelessScoreResponse
from src.services.recommendation.recommendation_service import (
    RecommendationResult,
    RecommendationService,
)

logger = get_logger(__name__)

# Completeness weights mirroring ProfileService's weighting scheme, kept
# separate rather than imported: the ORM-based ProfileService computes
# completeness from a persisted UserProfile row, while this computes it
# from a plain client-supplied dict. Duplicating a small weight table is
# preferable to coupling stateless (DB-free) logic to an ORM model.
_COMPLETENESS_WEIGHTS: dict[str, float] = {
    "education_level": 0.15,
    "current_field": 0.15,
    "years_of_experience": 0.10,
    "country": 0.05,
    "primary_goal": 0.20,
    "career_concerns": 0.10,
    "desired_work_environment": 0.10,
    "age_range": 0.05,
    "has_assessment": 0.10,
}


def _compute_stateless_completeness(
    profile: StatelessProfileMeta,
    has_assessment: bool,
) -> float:
    """Return a completeness score in [0, 100] for a client-supplied profile."""
    score = 0.0
    for field, weight in _COMPLETENESS_WEIGHTS.items():
        if field == "has_assessment":
            if has_assessment:
                score += weight
        elif field == "career_concerns":
            if profile.career_concerns:
                score += weight
        elif getattr(profile, field, None):
            score += weight
    return round(score * 100, 1)


class StatelessService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # RecommendationService still needs a DB session — solely to read
        # the shared career catalog and FAISS index, never per-user data.
        self.recommendation_service = RecommendationService(db)

    def get_questions(self, assessment_type: str) -> StatelessQuestionsResponse:
        """Return the static question bank for the given assessment type."""
        questions = get_questions_for_type(assessment_type)
        return StatelessQuestionsResponse(
            questions=[
                QuestionSchema(
                    id=q.id,
                    dimension=q.dimension.value,
                    prompt=q.prompt,
                    reverse_scored=q.reverse_scored,
                )
                for q in questions
            ],
            total_questions=len(questions),
        )

    def score_assessment(self, payload: StatelessScoreRequest) -> StatelessScoreResponse:
        """Score Likert responses without persisting anything."""
        scoring_result = score_responses(payload.responses)

        return StatelessScoreResponse(
            model_version=scoring_result.model_version,
            dimension_scores=[
                DimensionScoreSchema(
                    dimension=ds.dimension,
                    display_name=DIMENSION_METADATA[ds.dimension].display_name,
                    description=DIMENSION_METADATA[ds.dimension].description,
                    score=ds.score,
                    confidence=ds.confidence,
                    item_count=ds.item_count,
                    low_label=DIMENSION_METADATA[ds.dimension].low_label,
                    high_label=DIMENSION_METADATA[ds.dimension].high_label,
                )
                for ds in scoring_result.dimension_scores
            ],
        )

    async def get_recommendations(
        self,
        user_id: str,
        payload: StatelessRecommendationRequest,
    ) -> RecommendationResult:
        """
        Generate recommendations from client-supplied scores and profile
        data. Raises HTTP 400 (via RecommendationService) if
        dimension_scores is empty.
        """
        profile_meta: dict[str, str | None] = {
            "education_level": payload.profile.education_level,
            "current_field": payload.profile.current_field,
            "primary_goal": payload.profile.primary_goal,
        }
        has_assessment = bool(payload.dimension_scores)
        completeness = _compute_stateless_completeness(payload.profile, has_assessment)

        logger.info("Stateless recommendation request", user_id=user_id)

        return await self.recommendation_service.recommend_from_data(
            user_id=user_id,
            score_map=payload.dimension_scores,
            profile_meta=profile_meta,
            profile_completeness=completeness,
            top_k=payload.top_k,
        )
