"""Unit tests for the profile service completeness scoring."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.services.profile.profile_service import _compute_completeness


class TestCompletenessScoring:
    def _make_profile(self, **kwargs) -> MagicMock:  # type: ignore[no-untyped-def]
        """Build a mock UserProfile with all fields defaulting to None."""
        profile = MagicMock()
        profile.education_level = None
        profile.current_field = None
        profile.years_of_experience = None
        profile.country = None
        profile.primary_goal = None
        profile.career_concerns = None
        profile.desired_work_environment = None
        profile.age_range = None
        for k, v in kwargs.items():
            setattr(profile, k, v)
        return profile

    def test_empty_profile_scores_zero(self) -> None:
        profile = self._make_profile()
        score = _compute_completeness(profile, has_assessment=False)
        assert score == 0.0

    def test_full_profile_with_assessment_scores_100(self) -> None:
        profile = self._make_profile(
            education_level="Bachelor's degree",
            current_field="Technology",
            years_of_experience=5,
            country="India",
            primary_goal="Become an architect",
            career_concerns=["work-life balance"],
            desired_work_environment="Remote",
            age_range="25-34",
        )
        score = _compute_completeness(profile, has_assessment=True)
        assert score == pytest.approx(100.0, abs=0.1)

    def test_assessment_adds_to_score(self) -> None:
        profile = self._make_profile(primary_goal="Lead teams")
        without = _compute_completeness(profile, has_assessment=False)
        with_assessment = _compute_completeness(profile, has_assessment=True)
        assert with_assessment > without

    def test_career_concerns_empty_list_does_not_score(self) -> None:
        profile_no_concerns = self._make_profile(career_concerns=[])
        profile_with_concerns = self._make_profile(career_concerns=["balance"])
        score_no = _compute_completeness(profile_no_concerns, has_assessment=False)
        score_with = _compute_completeness(profile_with_concerns, has_assessment=False)
        assert score_with > score_no

    def test_score_is_in_valid_range(self) -> None:
        profile = self._make_profile(education_level="PhD", country="US")
        score = _compute_completeness(profile, has_assessment=False)
        assert 0.0 <= score <= 100.0

    def test_partial_profile_gives_partial_score(self) -> None:
        profile = self._make_profile(
            education_level="Bachelor's degree",
            primary_goal="Grow as a developer",
        )
        score = _compute_completeness(profile, has_assessment=False)
        assert 0.0 < score < 100.0
