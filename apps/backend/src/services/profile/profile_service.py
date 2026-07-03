"""
Profile service.

Handles reading, updating, and computing completeness for user profiles.
Also triggers embedding regeneration when profile fields change.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.embeddings.embedder import build_profile_text, embed_text
from src.core.logging.setup import get_logger
from src.db.models.profile import PsychometricScore, UserProfile
from src.db.repositories.psychometric import PsychometricScoreRepository

logger = get_logger(__name__)

# Weights used to compute completeness score (must sum to 1.0)
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


def _compute_completeness(profile: UserProfile, has_assessment: bool) -> float:
    """Return a completeness score in [0, 100]."""
    score = 0.0
    for field, weight in _COMPLETENESS_WEIGHTS.items():
        if field == "has_assessment":
            if has_assessment:
                score += weight
        elif field == "career_concerns":
            val = getattr(profile, field, None)
            if val and len(val) > 0:
                score += weight
        else:
            if getattr(profile, field, None):
                score += weight
    return round(score * 100, 1)


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.score_repo = PsychometricScoreRepository(db)

    async def get_profile(self, user_id: uuid.UUID) -> UserProfile:
        """Return the user's profile, raising 404 if not found."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Complete onboarding to create one.",
            )
        return profile

    async def get_or_create_profile(self, user_id: uuid.UUID) -> UserProfile:
        """Return existing profile or create a blank one."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = UserProfile(
                id=uuid.uuid4(),
                user_id=user_id,
                onboarding_completed=False,
                onboarding_step=0,
                completeness_score=0.0,
            )
            self.db.add(profile)
            await self.db.flush()
            await self.db.refresh(profile)
            logger.info("Created blank profile", user_id=str(user_id))
        return profile

    async def update_profile(
        self,
        user_id: uuid.UUID,
        updates: dict,
    ) -> UserProfile:
        """
        Partially update profile fields and recompute completeness.

        Allowed update keys: education_level, current_field, years_of_experience,
        country, primary_goal, career_concerns, desired_work_environment,
        age_range, onboarding_step, onboarding_completed.
        """
        profile = await self.get_or_create_profile(user_id)

        allowed_fields = {
            "education_level",
            "current_field",
            "years_of_experience",
            "country",
            "primary_goal",
            "career_concerns",
            "desired_work_environment",
            "age_range",
            "onboarding_step",
            "onboarding_completed",
        }

        for key, value in updates.items():
            if key in allowed_fields:
                setattr(profile, key, value)

        # Recompute completeness
        scores = await self.score_repo.get_latest_for_profile(profile.id)
        has_assessment = len(scores) > 0
        profile.completeness_score = _compute_completeness(profile, has_assessment)

        # Regenerate embedding if meaningful fields changed
        embedding_fields = {
            "education_level",
            "current_field",
            "primary_goal",
        }
        if embedding_fields & set(updates.keys()):
            await self._regenerate_embedding(profile, scores)

        await self.db.flush()
        await self.db.refresh(profile)

        logger.info(
            "Profile updated",
            user_id=str(user_id),
            completeness=profile.completeness_score,
        )
        return profile

    async def refresh_completeness(self, user_id: uuid.UUID) -> UserProfile:
        """Recompute and persist the completeness score without changing other fields."""
        profile = await self.get_profile(user_id)
        scores = await self.score_repo.get_latest_for_profile(profile.id)
        profile.completeness_score = _compute_completeness(profile, len(scores) > 0)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def _regenerate_embedding(
        self,
        profile: UserProfile,
        scores: list[PsychometricScore],
    ) -> None:
        """Recompute and store the profile embedding vector."""
        score_map = {s.dimension: s.score for s in scores}
        profile_meta: dict[str, str | None] = {
            "education_level": profile.education_level,
            "current_field": profile.current_field,
            "primary_goal": profile.primary_goal,
        }
        text = build_profile_text(score_map, profile_meta)
        profile.profile_embedding = embed_text(text)
        profile.embedding_updated_at = datetime.datetime.now(tz=datetime.UTC)
        logger.info("Profile embedding regenerated", user_id=str(profile.user_id))
