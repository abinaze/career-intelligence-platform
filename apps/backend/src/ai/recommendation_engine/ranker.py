"""
Multi-factor career recommendation ranker.

Re-ranks raw FAISS cosine-similarity hits using a weighted composite of:

    semantic similarity   50%  — vector distance between profile and career
    RIASEC interest match 30%  — alignment of user interests vs career interests
    salary percentile     10%  — normalised median salary
    outlook percentile    10%  — BLS projected job-growth outlook

Final composite score is in [0, 1]. Weights can be overridden per call.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.ai.psychometric_engine.dimensions import PsychometricDimension

_ONET_INTEREST_MAP: dict[str, str] = {
    "Realistic": PsychometricDimension.REALISTIC.value,
    "Investigative": PsychometricDimension.INVESTIGATIVE.value,
    "Artistic": PsychometricDimension.ARTISTIC.value,
    "Social": PsychometricDimension.SOCIAL.value,
    "Enterprising": PsychometricDimension.ENTERPRISING.value,
    "Conventional": PsychometricDimension.CONVENTIONAL.value,
}

DEFAULT_WEIGHTS: dict[str, float] = {
    "similarity": 0.50,
    "riasec": 0.30,
    "salary": 0.10,
    "outlook": 0.10,
}


@dataclass
class RankInput:
    """All data required to rank one candidate career."""

    onet_code: str
    career_id: str
    title: str
    similarity_score: float
    interests: dict | None
    median_salary_usd: float | None
    outlook_percentile: float | None


@dataclass
class RankedCareer:
    """A career candidate after composite re-ranking."""

    onet_code: str
    career_id: str
    title: str
    composite_score: float
    similarity_score: float
    riasec_score: float
    salary_score: float
    outlook_score: float


def _riasec_score(user_scores: dict[str, float], career_interests: dict | None) -> float:
    """Dot-product RIASEC interest alignment, normalised to [0, 1]."""
    if not career_interests:
        return 0.5
    user_vec: list[float] = []
    career_vec: list[float] = []
    for onet_label, dim_name in _ONET_INTEREST_MAP.items():
        user_vec.append(user_scores.get(dim_name, 50.0) / 100.0)
        career_vec.append(float(career_interests.get(onet_label, 0)) / 100.0)
    dot = sum(u * c for u, c in zip(user_vec, career_vec, strict=False))
    return min(dot / max(len(user_vec), 1), 1.0)


def _salary_score(salary: float | None, max_salary: float) -> float:
    if salary is None or max_salary <= 0:
        return 0.5
    return min(salary / max_salary, 1.0)


def rank_candidates(
    candidates: list[RankInput],
    user_scores: dict[str, float],
    weights: dict[str, float] | None = None,
) -> list[RankedCareer]:
    """
    Re-rank a list of FAISS candidate careers using composite scoring.

    Args:
        candidates:  raw similarity hits from the FAISS index.
        user_scores: dimension name → score (0-100) from the psychometric engine.
        weights:     optional override of DEFAULT_WEIGHTS.

    Returns:
        List of RankedCareer sorted by composite_score descending.
    """
    w = weights or DEFAULT_WEIGHTS
    salaries = [c.median_salary_usd for c in candidates if c.median_salary_usd]
    max_salary = max(salaries, default=0.0)

    ranked: list[RankedCareer] = []
    for c in candidates:
        riasec = _riasec_score(user_scores, c.interests)
        salary = _salary_score(c.median_salary_usd, max_salary)
        outlook = (c.outlook_percentile or 50.0) / 100.0
        composite = (
            w["similarity"] * c.similarity_score
            + w["riasec"] * riasec
            + w["salary"] * salary
            + w["outlook"] * outlook
        )
        ranked.append(
            RankedCareer(
                onet_code=c.onet_code,
                career_id=c.career_id,
                title=c.title,
                composite_score=round(composite, 4),
                similarity_score=round(c.similarity_score, 4),
                riasec_score=round(riasec, 4),
                salary_score=round(salary, 4),
                outlook_score=round(outlook, 4),
            )
        )
    return sorted(ranked, key=lambda x: x.composite_score, reverse=True)
