"""Database queries for psychometric scores and assessment sessions."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.profile import AssessmentSession, PsychometricScore
from src.db.repositories.base import BaseRepository


class PsychometricScoreRepository(BaseRepository[PsychometricScore]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(PsychometricScore, db)

    async def get_latest_for_profile(self, profile_id: uuid.UUID) -> list[PsychometricScore]:
        """Return the most recent score for each dimension for a profile."""
        result = await self.db.execute(
            select(PsychometricScore)
            .where(PsychometricScore.profile_id == profile_id)
            .order_by(PsychometricScore.dimension, PsychometricScore.created_at.desc())
        )
        scores = list(result.scalars().all())

        latest_by_dimension: dict[str, PsychometricScore] = {}
        for score in scores:
            if score.dimension not in latest_by_dimension:
                latest_by_dimension[score.dimension] = score

        return list(latest_by_dimension.values())


class AssessmentSessionRepository(BaseRepository[AssessmentSession]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AssessmentSession, db)

    async def get_active_session(
        self, user_id: uuid.UUID, assessment_type: str
    ) -> AssessmentSession | None:
        """Fetch an in-progress session of the given type for a user, if any."""
        result = await self.db.execute(
            select(AssessmentSession).where(
                AssessmentSession.user_id == user_id,
                AssessmentSession.assessment_type == assessment_type,
                AssessmentSession.status == "in_progress",
            )
        )
        return result.scalar_one_or_none()

    async def mark_completed(
        self, session_id: uuid.UUID, raw_scores: dict
    ) -> AssessmentSession | None:
        """Mark a session as completed and store its raw scores."""
        return await self.update_by_id(
            session_id,
            status="completed",
            completed_at=datetime.datetime.now(tz=datetime.UTC),
            raw_scores=raw_scores,
        )
