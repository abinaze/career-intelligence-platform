"""Service layer for psychometric assessment sessions."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.psychometric_engine.dimensions import DIMENSION_METADATA, PsychometricDimension
from src.ai.psychometric_engine.question_bank import QUESTION_BANK, LikertQuestion
from src.ai.psychometric_engine.scorer import score_responses
from src.core.logging.setup import get_logger
from src.db.models.profile import AssessmentSession, PsychometricScore
from src.db.repositories.psychometric import (
    AssessmentSessionRepository,
    PsychometricScoreRepository,
)
from src.db.repositories.user import UserRepository
from src.schemas.requests.assessment import StartAssessmentRequest, SubmitAssessmentRequest
from src.schemas.responses.assessment import (
    AssessmentResultSchema,
    AssessmentSessionSchema,
    DimensionScoreSchema,
    QuestionSchema,
)

logger = get_logger(__name__)

_QUICK_DIMENSIONS = {
    PsychometricDimension.OPENNESS,
    PsychometricDimension.CONSCIENTIOUSNESS,
    PsychometricDimension.EXTRAVERSION,
    PsychometricDimension.AGREEABLENESS,
    PsychometricDimension.NEUROTICISM,
}


def _get_questions(assessment_type: str) -> list[LikertQuestion]:
    if assessment_type == "quick":
        return [q for q in QUESTION_BANK if q.dimension in _QUICK_DIMENSIONS]
    return list(QUESTION_BANK)


class AssessmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.session_repo = AssessmentSessionRepository(db)
        self.score_repo = PsychometricScoreRepository(db)
        self.user_repo = UserRepository(db)

    async def start_session(
        self, user_id: uuid.UUID, payload: StartAssessmentRequest
    ) -> AssessmentSessionSchema:
        """Create a new assessment session and return questions."""
        session = AssessmentSession(
            id=uuid.uuid4(),
            user_id=user_id,
            assessment_type=payload.assessment_type,
            status="in_progress",
            started_at=datetime.datetime.now(tz=datetime.UTC),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        questions = _get_questions(payload.assessment_type)
        logger.info(
            "Assessment session started",
            session_id=str(session.id),
            user_id=str(user_id),
            question_count=len(questions),
        )

        return AssessmentSessionSchema(
            session_id=session.id,
            assessment_type=session.assessment_type,
            status=session.status,
            started_at=session.started_at,
            questions=[
                QuestionSchema(
                    id=q.id,
                    dimension=q.dimension.value,
                    prompt=q.prompt,
                    reverse_scored=q.reverse_scored,
                )
                for q in questions
            ],
        )

    async def submit_responses(
        self, user_id: uuid.UUID, payload: SubmitAssessmentRequest
    ) -> AssessmentResultSchema:
        """Score responses, persist results, return dimension scores."""
        session = await self.session_repo.get_by_id(uuid.UUID(payload.session_id))
        if not session or str(session.user_id) != str(user_id):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment session not found",
            )

        if session.status != "in_progress":
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is already completed",
            )

        scoring_result = score_responses(payload.responses)

        # Persist scores — get or create user profile
        from sqlalchemy import select
        from src.db.models.profile import UserProfile

        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        if profile:
            for ds in scoring_result.dimension_scores:
                if ds.item_count == 0:
                    continue
                score_row = PsychometricScore(
                    id=uuid.uuid4(),
                    profile_id=profile.id,
                    dimension=ds.dimension.value,
                    score=ds.score,
                    confidence=ds.confidence,
                    model_version=scoring_result.model_version,
                    assessment_session_id=session.id,
                )
                self.db.add(score_row)

        completed_at = datetime.datetime.now(tz=datetime.UTC)
        session.status = "completed"
        session.completed_at = completed_at
        session.responses = payload.responses
        session.raw_scores = {
            ds.dimension.value: {"score": ds.score, "confidence": ds.confidence}
            for ds in scoring_result.dimension_scores
        }
        await self.db.commit()

        logger.info(
            "Assessment session completed",
            session_id=str(session.id),
            user_id=str(user_id),
        )

        return AssessmentResultSchema(
            session_id=session.id,
            model_version=scoring_result.model_version,
            completed_at=completed_at,
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

    async def get_results(
        self, user_id: uuid.UUID, session_id: uuid.UUID
    ) -> AssessmentResultSchema:
        """Retrieve completed assessment results."""
        session = await self.session_repo.get_by_id(session_id)
        if not session or str(session.user_id) != str(user_id):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment session not found",
            )

        if session.status != "completed" or not session.raw_scores:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment not yet completed",
            )

        dimension_scores = []
        for dim in PsychometricDimension:
            raw = session.raw_scores.get(dim.value, {})
            meta = DIMENSION_METADATA[dim]
            dimension_scores.append(
                DimensionScoreSchema(
                    dimension=dim,
                    display_name=meta.display_name,
                    description=meta.description,
                    score=raw.get("score", 0.0),
                    confidence=raw.get("confidence", 0.0),
                    item_count=0,
                    low_label=meta.low_label,
                    high_label=meta.high_label,
                )
            )

        return AssessmentResultSchema(
            session_id=session.id,
            model_version="psychometric-v1",
            completed_at=session.completed_at,
            dimension_scores=dimension_scores,
        )
