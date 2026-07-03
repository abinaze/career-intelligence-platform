"""
Recommendation explainability engine.

Produces structured, human-readable explanations for each career
recommendation so users understand *why* a career was suggested.

Each explanation contains:
    - A top-level summary sentence.
    - Per-factor driver labels and detail sentences.
    - The top RIASEC traits that aligned with this career.
    - A confidence band: high / medium / low.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.ai.psychometric_engine.dimensions import DIMENSION_METADATA, PsychometricDimension
from src.ai.recommendation_engine.ranker import RankedCareer

_ONET_INTEREST_MAP: dict[str, str] = {
    "Realistic": PsychometricDimension.REALISTIC.value,
    "Investigative": PsychometricDimension.INVESTIGATIVE.value,
    "Artistic": PsychometricDimension.ARTISTIC.value,
    "Social": PsychometricDimension.SOCIAL.value,
    "Enterprising": PsychometricDimension.ENTERPRISING.value,
    "Conventional": PsychometricDimension.CONVENTIONAL.value,
}


@dataclass
class FactorExplanation:
    """Explanation for one composite scoring factor."""

    factor: str
    label: str
    score: float
    driver: str    # "strong match" | "moderate match" | "partial match" | "weak match"
    detail: str


@dataclass
class CareerExplanation:
    """Full structured explanation for one career recommendation."""

    career_id: str
    onet_code: str
    title: str
    summary: str
    confidence_band: str    # "high" | "medium" | "low"
    factors: list[FactorExplanation] = field(default_factory=list)
    top_matching_traits: list[str] = field(default_factory=list)


def _driver_label(score: float) -> str:
    if score >= 0.75:
        return "strong match"
    if score >= 0.50:
        return "moderate match"
    if score >= 0.25:
        return "partial match"
    return "weak match"


def _confidence_band(composite: float) -> str:
    if composite >= 0.70:
        return "high"
    if composite >= 0.45:
        return "medium"
    return "low"


def _top_traits(
    user_scores: dict[str, float],
    career_interests: dict | None,
    top_n: int = 3,
) -> list[str]:
    """Return display names of the RIASEC dims most aligned with this career."""
    if not career_interests:
        return []
    aligned: list[tuple[str, float]] = []
    for onet_label, dim_value in _ONET_INTEREST_MAP.items():
        career_score = float(career_interests.get(onet_label, 0)) / 100.0
        user_score = user_scores.get(dim_value, 50.0) / 100.0
        alignment = career_score * user_score
        if alignment > 0.1:
            dim = PsychometricDimension(dim_value)
            aligned.append((DIMENSION_METADATA[dim].display_name, alignment))
    aligned.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in aligned[:top_n]]


def explain(
    ranked: RankedCareer,
    user_scores: dict[str, float],
    career_interests: dict | None,
    career_description: str = "",
) -> CareerExplanation:
    """
    Build a structured explanation for a single ranked career.

    Args:
        ranked:             the re-ranked career record.
        user_scores:        dimension name → score (0-100).
        career_interests:   O*NET interest data or None.
        career_description: short description for context.
    """
    factors: list[FactorExplanation] = [
        FactorExplanation(
            factor="semantic_match",
            label="Profile–career semantic similarity",
            score=ranked.similarity_score,
            driver=_driver_label(ranked.similarity_score),
            detail=(
                f"Your overall profile aligns with {ranked.title} "
                f"at {ranked.similarity_score:.0%} semantic similarity."
            ),
        ),
        FactorExplanation(
            factor="riasec_alignment",
            label="Vocational interest alignment",
            score=ranked.riasec_score,
            driver=_driver_label(ranked.riasec_score),
            detail=(
                f"Your RIASEC interest profile overlaps with the typical "
                f"interests required for {ranked.title}."
            ),
        ),
        FactorExplanation(
            factor="salary",
            label="Salary competitiveness",
            score=ranked.salary_score,
            driver=_driver_label(ranked.salary_score),
            detail=(
                "Salary is benchmarked relative to all other recommended careers."
                if ranked.salary_score > 0
                else "Salary data not available for this occupation."
            ),
        ),
        FactorExplanation(
            factor="outlook",
            label="Job market outlook",
            score=ranked.outlook_score,
            driver=_driver_label(ranked.outlook_score),
            detail=(
                f"This occupation ranks at the "
                f"{ranked.outlook_score:.0%} percentile for projected job growth."
            ),
        ),
    ]

    top_traits = _top_traits(user_scores, career_interests)
    confidence = _confidence_band(ranked.composite_score)

    if top_traits:
        trait_str = " and ".join(top_traits[:2])
        summary = (
            f"{ranked.title} is a {confidence}-confidence match based on your "
            f"{trait_str} orientation and overall profile alignment."
        )
    else:
        summary = (
            f"{ranked.title} is a {confidence}-confidence match "
            f"based on your overall profile alignment."
        )

    return CareerExplanation(
        career_id=ranked.career_id,
        onet_code=ranked.onet_code,
        title=ranked.title,
        summary=summary,
        confidence_band=confidence,
        factors=factors,
        top_matching_traits=top_traits,
    )
