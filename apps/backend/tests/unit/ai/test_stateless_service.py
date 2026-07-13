"""Unit tests for the stateless (no-persistence) service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.ai.psychometric_engine.question_bank import QUESTION_BANK, get_questions_for_type
from src.schemas.requests.stateless import StatelessProfileMeta, StatelessScoreRequest
from src.services.stateless.stateless_service import (
    StatelessService,
    _compute_stateless_completeness,
)


class TestQuestionBankHelpers:
    def test_full_type_returns_all_questions(self) -> None:
        questions = get_questions_for_type("full")
        assert len(questions) == len(QUESTION_BANK)

    def test_quick_type_returns_fewer_questions(self) -> None:
        full = get_questions_for_type("full")
        quick = get_questions_for_type("quick")
        assert len(quick) < len(full)
        assert len(quick) > 0

    def test_unknown_type_defaults_to_full(self) -> None:
        questions = get_questions_for_type("something_else")
        assert len(questions) == len(QUESTION_BANK)


class TestStatelessCompleteness:
    def test_empty_profile_no_assessment_scores_zero(self) -> None:
        profile = StatelessProfileMeta()
        assert _compute_stateless_completeness(profile, has_assessment=False) == 0.0

    def test_full_profile_with_assessment_scores_100(self) -> None:
        profile = StatelessProfileMeta(
            education_level="Bachelor's degree",
            current_field="Technology",
            years_of_experience=5,
            country="India",
            primary_goal="Become an architect",
            career_concerns=["work-life balance"],
            desired_work_environment="Remote",
            age_range="25-34",
        )
        score = _compute_stateless_completeness(profile, has_assessment=True)
        assert score == pytest.approx(100.0, abs=0.1)

    def test_assessment_flag_increases_score(self) -> None:
        profile = StatelessProfileMeta(primary_goal="Grow as a developer")
        without = _compute_stateless_completeness(profile, has_assessment=False)
        with_assessment = _compute_stateless_completeness(profile, has_assessment=True)
        assert with_assessment > without

    def test_empty_career_concerns_list_does_not_score(self) -> None:
        no_concerns = StatelessProfileMeta(career_concerns=[])
        with_concerns = StatelessProfileMeta(career_concerns=["balance"])
        assert _compute_stateless_completeness(
            no_concerns, has_assessment=False
        ) < _compute_stateless_completeness(with_concerns, has_assessment=False)


class TestStatelessServiceGetQuestions:
    def test_get_questions_returns_correct_count(self) -> None:
        service = StatelessService(MagicMock())
        response = service.get_questions("full")
        assert response.total_questions == len(QUESTION_BANK)
        assert len(response.questions) == response.total_questions

    def test_get_questions_quick_type(self) -> None:
        service = StatelessService(MagicMock())
        response = service.get_questions("quick")
        assert response.total_questions < len(QUESTION_BANK)


class TestStatelessServiceScoreAssessment:
    def test_score_assessment_returns_all_dimensions(self) -> None:
        service = StatelessService(MagicMock())
        responses = {q.id: 4 for q in QUESTION_BANK}
        result = service.score_assessment(StatelessScoreRequest(responses=responses))
        assert len(result.dimension_scores) == 11
        for ds in result.dimension_scores:
            assert 0.0 <= ds.score <= 100.0
            assert 0.0 <= ds.confidence <= 1.0

    def test_score_assessment_partial_responses(self) -> None:
        service = StatelessService(MagicMock())
        # Only answer the first 5 questions
        responses = {q.id: 3 for q in QUESTION_BANK[:5]}
        result = service.score_assessment(StatelessScoreRequest(responses=responses))
        assert len(result.dimension_scores) == 11
