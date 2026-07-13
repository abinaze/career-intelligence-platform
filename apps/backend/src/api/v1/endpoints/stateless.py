"""
Stateless (no-persistence) API endpoints.

Backs local-device and bring-your-own-storage frontend flows. All
endpoints require authentication (a valid account is still needed), but
none of them read or write personal profile or assessment data to the
database — only the shared career catalog is read. See
docs/architecture/byos.md for the full design rationale.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_current_user
from src.db.engine import get_db
from src.db.models.user import User
from src.schemas.requests.stateless import StatelessRecommendationRequest, StatelessScoreRequest
from src.schemas.responses.recommendation import RecommendationResultSchema
from src.schemas.responses.stateless import StatelessQuestionsResponse, StatelessScoreResponse
from src.services.stateless.stateless_service import StatelessService

router = APIRouter(prefix="/stateless", tags=["Stateless (BYOS)"])


async def get_stateless_service(
    db: AsyncSession = Depends(get_db),
) -> StatelessService:
    return StatelessService(db)


@router.get(
    "/questions",
    response_model=StatelessQuestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the static assessment question bank (no session created)",
    description=(
        "Returns the question set for local-device or bring-your-own-storage "
        "assessment flows. Unlike POST /assessment/start, this does not "
        "create a database-tracked session."
    ),
)
async def get_questions(
    assessment_type: str = Query(default="full"),
    current_user: User = Depends(get_current_user),
    service: StatelessService = Depends(get_stateless_service),
) -> StatelessQuestionsResponse:
    return service.get_questions(assessment_type)


@router.post(
    "/score",
    response_model=StatelessScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Score assessment responses without persisting them",
)
async def score_assessment(
    payload: StatelessScoreRequest,
    current_user: User = Depends(get_current_user),
    service: StatelessService = Depends(get_stateless_service),
) -> StatelessScoreResponse:
    return service.score_assessment(payload)


@router.post(
    "/recommendations",
    response_model=RecommendationResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Generate recommendations from client-supplied profile and scores",
)
async def get_stateless_recommendations(
    payload: StatelessRecommendationRequest,
    current_user: User = Depends(get_current_user),
    service: StatelessService = Depends(get_stateless_service),
) -> RecommendationResultSchema:
    result = await service.get_recommendations(str(current_user.id), payload)

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
