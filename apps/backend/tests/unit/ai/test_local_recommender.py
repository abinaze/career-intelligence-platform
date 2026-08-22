"""
Unit tests for local_recommender.py — the DB-free replacement for the
archived RecommendationService.recommend_from_data.

No mocking needed anywhere in this file: every dependency (embedder,
career_catalog, ranker, explainer) is now pure/local, which is itself
a meaningful improvement over the DB-backed version this replaces —
the old equivalent test would have needed a mocked AsyncSession and
mocked query results.
"""

from __future__ import annotations

from fastapi import HTTPException
import pytest

from src.ai.recommendation_engine import career_catalog
from src.ai.recommendation_engine.local_recommender import recommend_from_data


def _sample_scores() -> dict[str, float]:
    return {
        "realistic": 40.0,
        "investigative": 85.0,
        "artistic": 35.0,
        "social": 20.0,
        "enterprising": 30.0,
        "conventional": 55.0,
    }


class TestRecommendFromData:
    def test_empty_score_map_raises_400(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            recommend_from_data(
                user_id="local",
                score_map={},
                profile_meta={},
                profile_completeness=0.0,
            )
        assert exc_info.value.status_code == 400

    def test_returns_requested_number_of_recommendations(self) -> None:
        result = recommend_from_data(
            user_id="local",
            score_map=_sample_scores(),
            profile_meta={"current_field": "Technology"},
            profile_completeness=60.0,
            top_k=5,
        )
        assert len(result.recommendations) == 5
        assert result.warning is None

    def test_caps_at_catalog_size_when_top_k_is_larger(self) -> None:
        result = recommend_from_data(
            user_id="local",
            score_map=_sample_scores(),
            profile_meta={},
            profile_completeness=50.0,
            top_k=1000,
        )
        assert len(result.recommendations) == len(career_catalog.CAREERS)

    def test_recommendations_sorted_by_descending_composite_score(self) -> None:
        result = recommend_from_data(
            user_id="local",
            score_map=_sample_scores(),
            profile_meta={},
            profile_completeness=50.0,
            top_k=10,
        )
        scores = [r.composite_score for r in result.recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_strong_investigative_score_surfaces_investigative_careers_highly(self) -> None:
        """
        A profile with a dominant Investigative score should rank
        Investigative-heavy careers (Software Developers, Medical
        Scientists) above Social-heavy ones (Elementary School
        Teachers) — a basic sanity check that the ranking is actually
        responsive to the input, not just returning the catalog in a
        fixed order.
        """
        investigative_heavy_scores = {
            "realistic": 30.0,
            "investigative": 95.0,
            "artistic": 20.0,
            "social": 15.0,
            "enterprising": 20.0,
            "conventional": 40.0,
        }
        result = recommend_from_data(
            user_id="local",
            score_map=investigative_heavy_scores,
            profile_meta={},
            profile_completeness=50.0,
            top_k=10,
        )
        titles_in_order = [r.title for r in result.recommendations]
        top_three = titles_in_order[:3]
        assert "Elementary School Teachers" not in top_three

    def test_each_recommendation_has_a_complete_explanation(self) -> None:
        result = recommend_from_data(
            user_id="local",
            score_map=_sample_scores(),
            profile_meta={},
            profile_completeness=50.0,
            top_k=3,
        )
        for rec in result.recommendations:
            assert rec.explanation.onet_code == rec.onet_code
            assert rec.explanation.summary
            assert rec.explanation.factors

    def test_career_id_matches_onet_code_in_this_db_free_path(self) -> None:
        """
        There's no database-generated id in this path, so onet_code is
        used directly as career_id — this pins that deliberate choice
        (see local_recommender.py's own comment on RankInput) rather
        than letting it silently drift.
        """
        result = recommend_from_data(
            user_id="local",
            score_map=_sample_scores(),
            profile_meta={},
            profile_completeness=50.0,
            top_k=3,
        )
        for rec in result.recommendations:
            assert rec.career_id == rec.onet_code

    def test_user_id_is_passed_through_unchanged(self) -> None:
        result = recommend_from_data(
            user_id="local",
            score_map=_sample_scores(),
            profile_meta={},
            profile_completeness=50.0,
        )
        assert result.user_id == "local"
