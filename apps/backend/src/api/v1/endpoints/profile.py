"""User profile API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_current_user
from src.db.engine import get_db
from src.db.models.user import User
from src.schemas.responses.recommendation import ProfileSchema, ProfileUpdateSchema
from src.services.profile.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])


async def get_profile_service(
    db: AsyncSession = Depends(get_db),
) -> ProfileService:
    return ProfileService(db)


@router.get(
    "",
    response_model=ProfileSchema,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileSchema:
    profile = await service.get_or_create_profile(current_user.id)
    return ProfileSchema(
        id=str(profile.id),
        user_id=str(profile.user_id),
        age_range=profile.age_range,
        education_level=profile.education_level,
        current_field=profile.current_field,
        years_of_experience=profile.years_of_experience,
        country=profile.country,
        primary_goal=profile.primary_goal,
        career_concerns=profile.career_concerns,
        desired_work_environment=profile.desired_work_environment,
        onboarding_completed=profile.onboarding_completed,
        onboarding_step=profile.onboarding_step,
        completeness_score=profile.completeness_score,
    )


@router.patch(
    "",
    response_model=ProfileSchema,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Partially updates profile fields. Omitted fields are unchanged.",
)
async def update_profile(
    payload: ProfileUpdateSchema,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileSchema:
    updates = payload.model_dump(exclude_none=True)
    profile = await service.update_profile(current_user.id, updates)
    return ProfileSchema(
        id=str(profile.id),
        user_id=str(profile.user_id),
        age_range=profile.age_range,
        education_level=profile.education_level,
        current_field=profile.current_field,
        years_of_experience=profile.years_of_experience,
        country=profile.country,
        primary_goal=profile.primary_goal,
        career_concerns=profile.career_concerns,
        desired_work_environment=profile.desired_work_environment,
        onboarding_completed=profile.onboarding_completed,
        onboarding_step=profile.onboarding_step,
        completeness_score=profile.completeness_score,
    )
