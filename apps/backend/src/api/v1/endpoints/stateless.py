"""
Stateless (no-persistence) API endpoints.

Backs local-device and bring-your-own-storage frontend flows, and —
since the Cloud archive (see docs/NORTH_STAR.md) — the only assessment/
recommendation path this application has. No authentication: there is
no account system in the desktop-first product. Nothing here reads or
writes personal profile or assessment data to any database; only the
static, shared career catalog (career_catalog.py) is read, in memory.
See docs/architecture/byos.md for the original design rationale.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from src.schemas.requests.stateless import StatelessRecommendationRequest, StatelessScoreRequest
from src.schemas.responses.recommendation import RecommendationResultSchema
from src.schemas.responses.stateless import StatelessQuestionsResponse, StatelessScoreResponse
from src.services.stateless.stateless_service import StatelessService

router = APIRouter(prefix="/stateless", tags=["Stateless (BYOS)"])


def get_stateless_service() -> StatelessService:
    return StatelessService()


@router.get(
    "/questions",
    response_model=StatelessQuestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the static assessment question bank",
    description="Returns the question set for the assessment flow. Creates no session.",
)
def get_questions(
    assessment_type: str = Query(default="full"),
) -> StatelessQuestionsResponse:
    return get_stateless_service().get_questions(assessment_type)


@router.post(
    "/score",
    response_model=StatelessScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Score assessment responses without persisting them",
)
def score_assessment(
    payload: StatelessScoreRequest,
) -> StatelessScoreResponse:
    return get_stateless_service().score_assessment(payload)


@router.post(
    "/recommendations",
    response_model=RecommendationResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Generate recommendations from client-supplied profile and scores",
)
def get_stateless_recommendations(
    payload: StatelessRecommendationRequest,
) -> RecommendationResultSchema:
    # "local" rather than a real user id — there is no account system
    # in this path (see docs/NORTH_STAR.md); this label exists only for
    # the log line inside get_recommendations.
    result = get_stateless_service().get_recommendations("local", payload)

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
