"""
DB-free recommendation engine.

Replaces the DB-backed `RecommendationService.recommend_from_data`
(archived to archive/cloud/ along with the rest of the Cloud product —
see docs/NORTH_STAR.md) with the same pipeline running entirely against
the static `career_catalog` module: no Postgres, no FAISS, no
`AsyncSession`.

Pipeline, unchanged in shape from the archived version, just sourced
differently:
    1. Build profile text and embed it            (embedder.py, unchanged)
    2. Cosine-similarity search against the catalog (career_catalog.py, NumPy — not FAISS)
    3. Multi-factor re-rank                         (ranker.py, unchanged)
    4. Per-career explanation                       (explainability/explainer.py, unchanged)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import HTTPException, status

from src.ai.embeddings.embedder import build_profile_text, embed_text
from src.ai.explainability.explainer import CareerExplanation, explain
from src.ai.recommendation_engine import career_catalog
from src.ai.recommendation_engine.ranker import RankInput, rank_candidates
from src.core.logging.setup import get_logger

logger = get_logger(__name__)

_CANDIDATE_POOL_SIZE = 20  # candidates considered before re-ranking
_DEFAULT_RETURN = 10  # final recommendations returned to the caller


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
    """Full recommendation response for one request."""

    user_id: str
    profile_completeness: float
    recommendations: list[CareerRecommendation] = field(default_factory=list)
    warning: str | None = None


def recommend_from_data(
    user_id: str,
    score_map: dict[str, float],
    profile_meta: dict[str, str | None],
    profile_completeness: float,
    top_k: int = _DEFAULT_RETURN,
) -> RecommendationResult:
    """
    Core recommendation pipeline, given only client-supplied data.

    `user_id` is a caller-chosen label for logging only — there's no
    account system in this path (see docs/NORTH_STAR.md), so it's not
    looked up or validated against anything. Callers with no notion of
    a user id should pass a constant like "local".

    Raises:
        HTTPException(400) — score_map is empty (no assessment data supplied).
    """
    if not score_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed assessment found. Complete an assessment first.",
        )

    if not career_catalog.CAREERS:
        return RecommendationResult(
            user_id=user_id,
            profile_completeness=profile_completeness,
            recommendations=[],
            warning="Career catalog is empty.",
        )

    profile_text = build_profile_text(score_map, profile_meta)
    query_vector = embed_text(profile_text)

    hits = career_catalog.search(query_vector, top_k=_CANDIDATE_POOL_SIZE)

    rank_inputs = [
        RankInput(
            onet_code=career.onet_code,
            career_id=career.onet_code,  # no DB-generated id in this path — the
            # O*NET code is already a stable, unique natural key, so it's
            # used directly rather than inventing a synthetic UUID that
            # would mean nothing outside a database.
            title=career.title,
            similarity_score=similarity,
            interests=career.interests,
            median_salary_usd=career.median_salary_usd,
            outlook_percentile=career.outlook_percentile,
        )
        for career, similarity in hits
    ]

    ranked = rank_candidates(rank_inputs, score_map)

    catalog_by_onet = {c.onet_code: c for c in career_catalog.CAREERS}
    recommendations: list[CareerRecommendation] = []
    for rc in ranked[:top_k]:
        career = catalog_by_onet.get(rc.onet_code)
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
        "Recommendations generated (local, DB-free)",
        user_id=user_id,
        count=len(recommendations),
    )
    return RecommendationResult(
        user_id=user_id,
        profile_completeness=profile_completeness,
        recommendations=recommendations,
    )
