"""Assessment API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_current_user
from src.db.engine import get_db
from src.db.models.user import User
from src.schemas.requests.assessment import StartAssessmentRequest, SubmitAssessmentRequest
from src.schemas.responses.assessment import AssessmentResultSchema, AssessmentSessionSchema
from src.services.psychometric.assessment_service import AssessmentService

router = APIRouter(prefix="/assessment", tags=["Assessment"])


async def get_assessment_service(
    db: AsyncSession = Depends(get_db),
) -> AssessmentService:
    return AssessmentService(db)


@router.post(
    "/start",
    response_model=AssessmentSessionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new assessment session",
)
async def start_assessment(
    payload: StartAssessmentRequest,
    current_user: User = Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentSessionSchema:
    """Create a new psychometric assessment session and return the question set."""
    return await service.start_session(current_user.id, payload)


@router.post(
    "/submit",
    response_model=AssessmentResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Submit assessment responses and retrieve scores",
)
async def submit_assessment(
    payload: SubmitAssessmentRequest,
    current_user: User = Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentResultSchema:
    """Submit Likert responses, compute scores, and persist results."""
    return await service.submit_responses(current_user.id, payload)


@router.get(
    "/results/{session_id}",
    response_model=AssessmentResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Retrieve results for a completed assessment",
)
async def get_assessment_results(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentResultSchema:
    """Fetch scored results for a previously completed assessment session."""
    return await service.get_results(current_user.id, session_id)
