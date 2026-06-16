"""Unit tests for the psychometric scoring engine."""

from __future__ import annotations

import pytest

from src.ai.psychometric_engine.dimensions import PsychometricDimension
from src.ai.psychometric_engine.question_bank import QUESTION_BANK, get_question_by_id
from src.ai.psychometric_engine.scorer import (
    InvalidResponseError,
    score_responses,
)


class TestQuestionBank:
    def test_question_bank_not_empty(self) -> None:
        assert len(QUESTION_BANK) > 0

    def test_all_dimensions_have_questions(self) -> None:
        dimensions_covered = {q.dimension for q in QUESTION_BANK}
        assert dimensions_covered == set(PsychometricDimension)

    def test_question_ids_are_unique(self) -> None:
        ids = [q.id for q in QUESTION_BANK]
        assert len(ids) == len(set(ids))

    def test_get_question_by_id_found(self) -> None:
        first = QUESTION_BANK[0]
        result = get_question_by_id(first.id)
        assert result is not None
        assert result.id == first.id

    def test_get_question_by_id_not_found(self) -> None:
        assert get_question_by_id("does_not_exist") is None


class TestScorer:
    def test_all_max_responses_yield_high_scores_for_non_reversed(self) -> None:
        responses = {q.id: 5 for q in QUESTION_BANK}
        result = score_responses(responses)

        for ds in result.dimension_scores:
            questions = [q for q in QUESTION_BANK if q.dimension == ds.dimension]
            if all(not q.reverse_scored for q in questions):
                assert ds.score == pytest.approx(100.0)

    def test_reverse_scored_item_flips_score(self) -> None:
        reverse_question = next(q for q in QUESTION_BANK if q.reverse_scored)
        responses = {reverse_question.id: 1}

        result = score_responses(responses)
        ds = result.get_score(reverse_question.dimension)

        assert ds is not None
        # Raw 1 on a reverse-scored item should normalize to 100.
        assert ds.score == pytest.approx(100.0)

    def test_neutral_responses_yield_midpoint_score(self) -> None:
        responses = {q.id: 3 for q in QUESTION_BANK}
        result = score_responses(responses)

        for ds in result.dimension_scores:
            assert ds.score == pytest.approx(50.0)

    def test_unanswered_dimension_has_zero_confidence(self) -> None:
        # Answer only openness questions.
        openness_questions = [
            q for q in QUESTION_BANK if q.dimension == PsychometricDimension.OPENNESS
        ]
        responses = {q.id: 4 for q in openness_questions}

        result = score_responses(responses)

        unanswered = result.get_score(PsychometricDimension.CONSCIENTIOUSNESS)
        assert unanswered is not None
        assert unanswered.item_count == 0
        assert unanswered.confidence == 0.0
        assert unanswered.score == 0.0

    def test_partial_dimension_has_partial_confidence(self) -> None:
        openness_questions = [
            q for q in QUESTION_BANK if q.dimension == PsychometricDimension.OPENNESS
        ]
        total_openness = len(openness_questions)
        # Answer only the first item for this dimension.
        responses = {openness_questions[0].id: 4}

        result = score_responses(responses)
        ds = result.get_score(PsychometricDimension.OPENNESS)

        assert ds is not None
        assert ds.item_count == 1
        assert ds.confidence == pytest.approx(1 / total_openness)

    def test_full_dimension_has_full_confidence(self) -> None:
        openness_questions = [
            q for q in QUESTION_BANK if q.dimension == PsychometricDimension.OPENNESS
        ]
        responses = {q.id: 4 for q in openness_questions}

        result = score_responses(responses)
        ds = result.get_score(PsychometricDimension.OPENNESS)

        assert ds is not None
        assert ds.confidence == pytest.approx(1.0)

    def test_unknown_question_id_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_responses({"not_a_real_question": 3})

    def test_out_of_range_response_raises(self) -> None:
        question = QUESTION_BANK[0]

        with pytest.raises(InvalidResponseError):
            score_responses({question.id: 6})

        with pytest.raises(InvalidResponseError):
            score_responses({question.id: 0})

    def test_empty_responses_return_all_dimensions_with_zero_scores(self) -> None:
        result = score_responses({})

        assert len(result.dimension_scores) == len(PsychometricDimension)
        for ds in result.dimension_scores:
            assert ds.score == 0.0
            assert ds.confidence == 0.0
            assert ds.item_count == 0

    def test_result_includes_model_version(self) -> None:
        result = score_responses({})
        assert result.model_version
        assert isinstance(result.model_version, str)
