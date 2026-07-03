"""Unit tests for the recommendation engine components."""

from __future__ import annotations

from src.ai.embeddings.embedder import _fallback_embedding, build_profile_text, embed_text
from src.ai.explainability.explainer import _confidence_band, _driver_label, explain
from src.ai.recommendation_engine.ranker import RankedCareer, RankInput, rank_candidates


class TestEmbedder:
    def test_embed_text_returns_correct_dimension(self) -> None:
        from src.core.config.settings import get_settings

        dim = get_settings().EMBEDDING_DIMENSION
        result = embed_text("software engineering and data science")
        assert len(result) == dim

    def test_embed_empty_string_returns_zero_vector(self) -> None:
        from src.core.config.settings import get_settings

        dim = get_settings().EMBEDDING_DIMENSION
        result = embed_text("")
        assert result == [0.0] * dim

    def test_embed_whitespace_returns_zero_vector(self) -> None:
        from src.core.config.settings import get_settings

        dim = get_settings().EMBEDDING_DIMENSION
        result = embed_text("   ")
        assert result == [0.0] * dim

    def test_fallback_embedding_is_deterministic(self) -> None:
        a = _fallback_embedding("test text")
        b = _fallback_embedding("test text")
        assert a == b

    def test_fallback_embedding_different_texts_differ(self) -> None:
        a = _fallback_embedding("software developer")
        b = _fallback_embedding("registered nurse")
        assert a != b

    def test_fallback_embedding_is_unit_normalised(self) -> None:
        import math

        vec = _fallback_embedding("career test")
        magnitude = math.sqrt(sum(x**2 for x in vec))
        assert abs(magnitude - 1.0) < 1e-5

    def test_build_profile_text_includes_all_fields(self) -> None:
        scores = {"openness": 80.0, "conscientiousness": 60.0}
        meta = {
            "education_level": "Bachelor's degree",
            "current_field": "Technology",
            "primary_goal": "Become a data scientist",
        }
        text = build_profile_text(scores, meta)
        assert "Bachelor's degree" in text
        assert "Technology" in text
        assert "data scientist" in text
        assert "openness" in text

    def test_build_profile_text_empty_inputs_returns_fallback(self) -> None:
        text = build_profile_text({}, {})
        assert len(text) > 0


class TestRanker:
    def _make_candidate(
        self,
        onet_code: str = "15-1252.00",
        title: str = "Software Developer",
        similarity: float = 0.8,
        salary: float | None = 100_000.0,
        outlook: float | None = 80.0,
        interests: dict | None = None,
    ) -> RankInput:
        return RankInput(
            onet_code=onet_code,
            career_id=f"id-{onet_code}",
            title=title,
            similarity_score=similarity,
            interests=interests or {"Investigative": 85, "Realistic": 40},
            median_salary_usd=salary,
            outlook_percentile=outlook,
        )

    def test_rank_candidates_returns_sorted_descending(self) -> None:
        candidates = [
            self._make_candidate("A", similarity=0.4),
            self._make_candidate("B", similarity=0.9),
            self._make_candidate("C", similarity=0.6),
        ]
        user_scores = {"investigative": 80.0}
        ranked = rank_candidates(candidates, user_scores)
        scores = [r.composite_score for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_candidates_composite_in_range(self) -> None:
        candidates = [self._make_candidate()]
        ranked = rank_candidates(candidates, {"investigative": 70.0})
        assert 0.0 <= ranked[0].composite_score <= 1.0

    def test_rank_candidates_no_salary_uses_neutral(self) -> None:
        candidate = self._make_candidate(salary=None)
        ranked = rank_candidates([candidate], {})
        assert ranked[0].salary_score == 0.5

    def test_rank_candidates_empty_list_returns_empty(self) -> None:
        assert rank_candidates([], {}) == []

    def test_rank_candidates_no_interests_uses_neutral_riasec(self) -> None:
        candidate = self._make_candidate(interests=None)
        ranked = rank_candidates([candidate], {})
        assert ranked[0].riasec_score == 0.5


class TestExplainer:
    def _make_ranked(self, composite: float = 0.75) -> RankedCareer:
        return RankedCareer(
            onet_code="15-1252.00",
            career_id="test-id",
            title="Software Developer",
            composite_score=composite,
            similarity_score=0.8,
            riasec_score=0.7,
            salary_score=0.6,
            outlook_score=0.5,
        )

    def test_explain_returns_four_factors(self) -> None:
        ranked = self._make_ranked()
        result = explain(ranked, {}, None)
        assert len(result.factors) == 4

    def test_explain_high_composite_gives_high_confidence(self) -> None:
        ranked = self._make_ranked(composite=0.80)
        result = explain(ranked, {}, None)
        assert result.confidence_band == "high"

    def test_explain_low_composite_gives_low_confidence(self) -> None:
        ranked = self._make_ranked(composite=0.20)
        result = explain(ranked, {}, None)
        assert result.confidence_band == "low"

    def test_explain_summary_contains_career_title(self) -> None:
        ranked = self._make_ranked()
        result = explain(ranked, {}, None)
        assert "Software Developer" in result.summary

    def test_explain_with_interests_returns_matching_traits(self) -> None:
        interests = {"Investigative": 90, "Realistic": 70}
        user_scores = {"investigative": 85.0, "realistic": 60.0}
        ranked = self._make_ranked()
        result = explain(ranked, user_scores, interests)
        assert len(result.top_matching_traits) > 0

    def test_driver_label_thresholds(self) -> None:
        assert _driver_label(0.90) == "strong match"
        assert _driver_label(0.60) == "moderate match"
        assert _driver_label(0.35) == "partial match"
        assert _driver_label(0.10) == "weak match"

    def test_confidence_band_thresholds(self) -> None:
        assert _confidence_band(0.80) == "high"
        assert _confidence_band(0.55) == "medium"
        assert _confidence_band(0.30) == "low"
