"""
Psychometric scoring engine.

Computes normalized dimension scores (0-100) and confidence values from
raw Likert-scale assessment responses.
"""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel

from src.ai.psychometric_engine.dimensions import PsychometricDimension
from src.ai.psychometric_engine.question_bank import QUESTION_BANK, get_question_by_id

SCORER_MODEL_VERSION = "psychometric-v1"

# 5-point Likert scale bounds.
_LIKERT_MIN = 1
_LIKERT_MAX = 5

# Minimum number of answered items per dimension to reach full confidence.
_FULL_CONFIDENCE_ITEM_COUNT = 3


class DimensionScore(BaseModel):
    """A single computed dimension score with supporting metadata."""

    dimension: PsychometricDimension
    score: float
    confidence: float
    item_count: int
    raw_mean: float


class ScoringResult(BaseModel):
    """The full set of dimension scores for an assessment session."""

    model_version: str
    dimension_scores: list[DimensionScore]

    def get_score(self, dimension: PsychometricDimension) -> DimensionScore | None:
        """Return the score for a specific dimension, if present."""
        for ds in self.dimension_scores:
            if ds.dimension == dimension:
                return ds
        return None


class InvalidResponseError(ValueError):
    """Raised when a response payload contains invalid data."""


def _normalize_value(raw_value: int, reverse_scored: bool) -> float:
    """
    Normalize a raw 1-5 Likert response to a 0-100 scale.

    Reverse-scored items are flipped before normalization so that a
    higher normalized score always indicates a stronger expression of
    the underlying trait.
    """
    if reverse_scored:
        raw_value = (_LIKERT_MAX + _LIKERT_MIN) - raw_value

    value_range = _LIKERT_MAX - _LIKERT_MIN
    return ((raw_value - _LIKERT_MIN) / value_range) * 100.0


def _compute_confidence(item_count: int, expected_count: int) -> float:
    """
    Compute a confidence value (0.0-1.0) based on the proportion of
    expected items for a dimension that were answered.
    """
    if expected_count <= 0:
        return 0.0

    coverage = item_count / expected_count
    return round(min(coverage, 1.0), 4)


def score_responses(responses: dict[str, int]) -> ScoringResult:
    """
    Compute normalized dimension scores from a mapping of question IDs
    to raw Likert responses (1-5).

    Raises:
        InvalidResponseError: if a question ID is unknown or a response
            value is outside the valid 1-5 range.
    """
    expected_counts: dict[PsychometricDimension, int] = defaultdict(int)
    for question in QUESTION_BANK:
        expected_counts[question.dimension] += 1

    normalized_by_dimension: dict[PsychometricDimension, list[float]] = defaultdict(list)
    raw_by_dimension: dict[PsychometricDimension, list[int]] = defaultdict(list)

    for question_id, raw_value in responses.items():
        question = get_question_by_id(question_id)
        if question is None:
            raise InvalidResponseError(f"Unknown question id: {question_id!r}")

        if not _LIKERT_MIN <= raw_value <= _LIKERT_MAX:
            raise InvalidResponseError(
                f"Response for {question_id!r} must be between "
                f"{_LIKERT_MIN} and {_LIKERT_MAX}, got {raw_value}"
            )

        normalized = _normalize_value(raw_value, question.reverse_scored)
        normalized_by_dimension[question.dimension].append(normalized)
        raw_by_dimension[question.dimension].append(raw_value)

    dimension_scores: list[DimensionScore] = []
    for dimension in PsychometricDimension:
        normalized_values = normalized_by_dimension.get(dimension, [])
        raw_values = raw_by_dimension.get(dimension, [])
        item_count = len(normalized_values)

        if item_count == 0:
            score = 0.0
            raw_mean = 0.0
        else:
            score = round(sum(normalized_values) / item_count, 2)
            raw_mean = round(sum(raw_values) / item_count, 2)

        confidence = _compute_confidence(item_count, expected_counts[dimension])

        dimension_scores.append(
            DimensionScore(
                dimension=dimension,
                score=score,
                confidence=confidence,
                item_count=item_count,
                raw_mean=raw_mean,
            )
        )

    return ScoringResult(
        model_version=SCORER_MODEL_VERSION,
        dimension_scores=dimension_scores,
    )
