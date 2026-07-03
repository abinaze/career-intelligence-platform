"""Career recommendation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_current_user
from src.db.engine import get_db
from src.db.models.user import User
from src.schemas.responses.recommendation import RecommendationResultSchema
from src.services.recommendation.recommendation_service import RecommendationService

router = APIRouter(prefix="/careers", tags=["Careers"])


async def get_recommendation_service(
    db: AsyncSession = Depends(get_db),
) -> RecommendationService:
    return RecommendationService(db)


@router.get(
    "/recommendations",
    response_model=RecommendationResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Get personalised career recommendations",
    description=(
        "Returns ranked career recommendations based on the user's completed "
        "psychometric assessment. Requires at least one completed assessment."
    ),
)
async def get_recommendations(
    top_k: int = Query(default=10, ge=1, le=50, description="Number of results to return"),
    current_user: User = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResultSchema:
    result = await service.get_recommendations(current_user.id, top_k=top_k)

    return RecommendationResultSchema(
        user_id=result.user_id,
        profile_completeness=result.profile_completeness,
        warning=result.warning,
        recommendations=[
            {
                "career_id": r.career_id,
                "onet_code": r.onet_code,
                "title": r.title,
                "broad_category": r.broad_category,
                "description": r.description,
                "median_salary_usd": r.median_salary_usd,
                "outlook_percentile": r.outlook_percentile,
                "composite_score": r.composite_score,
                "similarity_score": r.similarity_score,
                "riasec_score": r.riasec_score,
                "explanation": {
                    "career_id": r.explanation.career_id,
                    "onet_code": r.explanation.onet_code,
                    "title": r.explanation.title,
                    "summary": r.explanation.summary,
                    "confidence_band": r.explanation.confidence_band,
                    "top_matching_traits": r.explanation.top_matching_traits,
                    "factors": [
                        {
                            "factor": f.factor,
                            "label": f.label,
                            "score": f.score,
                            "driver": f.driver,
                            "detail": f.detail,
                        }
                        for f in r.explanation.factors
                    ],
                },
            }
            for r in result.recommendations
        ],
    )
