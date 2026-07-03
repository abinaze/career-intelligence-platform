"""
Recommendation service.

Orchestrates the full recommendation pipeline:
    1. Load the user's profile and latest psychometric scores.
    2. Build a profile text representation and embed it.
    3. Query the FAISS index for the top-N semantically similar careers.
    4. Fetch full career records from the DB for the candidates.
    5. Re-rank using the multi-factor ranker.
    6. Generate per-career explanations.
    7. Return a structured RecommendationResult.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.embeddings.embedder import build_profile_text, embed_text
from src.ai.explainability.explainer import CareerExplanation, explain
from src.ai.recommendation_engine.faiss_index import career_index
from src.ai.recommendation_engine.ranker import RankInput, rank_candidates
from src.core.logging.setup import get_logger
from src.db.models.career import Career
from src.db.models.profile import UserProfile
from src.db.repositories.career import CareerRepository
from src.db.repositories.psychometric import PsychometricScoreRepository
from src.db.repositories.user import UserRepository

logger = get_logger(__name__)

_DEFAULT_FAISS_TOP_K = 20   # candidates fetched from FAISS before re-ranking
_DEFAULT_RETURN = 10        # final recommendations returned to client


@dataclass
class CareerRecommendation:
    """A single ranked and explained career recommendation."""

    career_id: str
    onet_code: str
    title: str
    broad_category: str
    description: str
    median_salary_usd: float | None
    outlook_percentile: float | None
    composite_score: float
    similarity_score: float
    riasec_score: float
    explanation: CareerExplanation


@dataclass
class RecommendationResult:
    """Full recommendation response for one user."""

    user_id: str
    profile_completeness: float
    recommendations: list[CareerRecommendation] = field(default_factory=list)
    warning: str | None = None


class RecommendationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.career_repo = CareerRepository(db)
        self.score_repo = PsychometricScoreRepository(db)
        self.user_repo = UserRepository(db)

    async def get_recommendations(
        self,
        user_id: uuid.UUID,
        top_k: int = _DEFAULT_RETURN,
    ) -> RecommendationResult:
        """
        Generate career recommendations for a user.

        Raises:
            HTTP 404 — user has no profile (complete onboarding first).
            HTTP 400 — no completed assessment exists.
        """
        # 1. Load profile
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Complete onboarding first.",
            )

        # 2. Load latest psychometric scores
        scores = await self.score_repo.get_latest_for_profile(profile.id)
        if not scores:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No completed assessment found. Complete an assessment first.",
            )
        score_map: dict[str, float] = {s.dimension: s.score for s in scores}

        # 3. Build profile text and embed
        profile_meta: dict[str, str | None] = {
            "education_level": profile.education_level,
            "current_field": profile.current_field,
            "primary_goal": profile.primary_goal,
        }
        profile_text = build_profile_text(score_map, profile_meta)
        query_vector = embed_text(profile_text)

        # 4. FAISS similarity search
        if not career_index.is_ready:
            logger.warning("FAISS index not ready — rebuilding from DB")
            await self._rebuild_index()

        similarity_hits = career_index.search(query_vector, top_k=_DEFAULT_FAISS_TOP_K)

        if not similarity_hits:
            return RecommendationResult(
                user_id=str(user_id),
                profile_completeness=profile.completeness_score,
                recommendations=[],
                warning="Career database is empty. Run: make load-onet",
            )

        # 5. Fetch full career records for candidates
        onet_codes = [hit.onet_code for hit in similarity_hits]
        career_records = await self._fetch_careers_by_onet(onet_codes)
        career_map: dict[str, Career] = {c.onet_code: c for c in career_records}

        rank_inputs: list[RankInput] = []
        for hit in similarity_hits:
            career = career_map.get(hit.onet_code)
            if not career:
                continue
            rank_inputs.append(
                RankInput(
                    onet_code=hit.onet_code,
                    career_id=hit.career_id,
                    title=hit.title,
                    similarity_score=hit.similarity_score,
                    interests=career.interests,
                    median_salary_usd=career.median_salary_usd,
                    outlook_percentile=career.outlook_percentile,
                )
            )

        # 6. Multi-factor re-ranking
        ranked = rank_candidates(rank_inputs, score_map)

        # 7. Build explanations and final response
        recommendations: list[CareerRecommendation] = []
        for rc in ranked[:top_k]:
            career = career_map.get(rc.onet_code)
            if not career:
                continue
            explanation = explain(
                ranked=rc,
                user_scores=score_map,
                career_interests=career.interests,
                career_description=career.description,
            )
            recommendations.append(
                CareerRecommendation(
                    career_id=rc.career_id,
                    onet_code=rc.onet_code,
                    title=rc.title,
                    broad_category=career.broad_category,
                    description=career.description,
                    median_salary_usd=career.median_salary_usd,
                    outlook_percentile=career.outlook_percentile,
                    composite_score=rc.composite_score,
                    similarity_score=rc.similarity_score,
                    riasec_score=rc.riasec_score,
                    explanation=explanation,
                )
            )

        logger.info(
            "Recommendations generated",
            user_id=str(user_id),
            count=len(recommendations),
        )
        return RecommendationResult(
            user_id=str(user_id),
            profile_completeness=profile.completeness_score,
            recommendations=recommendations,
        )

    async def _fetch_careers_by_onet(self, onet_codes: list[str]) -> list[Career]:
        result = await self.db.execute(
            select(Career).where(Career.onet_code.in_(onet_codes))
        )
        return list(result.scalars().all())

    async def _rebuild_index(self) -> None:
        """Reload all career embeddings from DB and rebuild the FAISS index."""
        careers = await self.career_repo.get_all_paginated(limit=10_000)
        career_index.build(
            [
                {
                    "id": str(c.id),
                    "onet_code": c.onet_code,
                    "title": c.title,
                    "embedding": c.embedding,
                }
                for c in careers
            ]
        )
