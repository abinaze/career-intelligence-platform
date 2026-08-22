"""Unit tests for the static, DB-free career catalog."""

from __future__ import annotations

import numpy as np
import pytest

from src.ai.recommendation_engine import career_catalog


class TestCareerCatalog:
    def test_catalog_has_ten_careers(self) -> None:
        # Verified precisely against src/scripts/load_onet.py's original
        # ONET_CAREERS list before this module existed — an earlier
        # planning document stated 14, which was wrong. This test pins
        # the real count so a future edit that silently drops or
        # duplicates an entry gets caught.
        assert len(career_catalog.CAREERS) == 10

    def test_every_career_has_a_unique_onet_code(self) -> None:
        codes = [c.onet_code for c in career_catalog.CAREERS]
        assert len(codes) == len(set(codes))

    def test_every_career_has_all_six_riasec_interests(self) -> None:
        expected = {
            "Realistic",
            "Investigative",
            "Artistic",
            "Social",
            "Enterprising",
            "Conventional",
        }
        for career in career_catalog.CAREERS:
            assert set(career.interests.keys()) == expected
            for value in career.interests.values():
                assert 0 <= value <= 100


class TestCareerCatalogSearch:
    def test_search_returns_requested_top_k(self) -> None:
        query = [0.1] * 384
        results = career_catalog.search(query, top_k=3)
        assert len(results) == 3

    def test_search_caps_top_k_at_catalog_size(self) -> None:
        query = [0.1] * 384
        results = career_catalog.search(query, top_k=1000)
        assert len(results) == len(career_catalog.CAREERS)

    def test_search_results_sorted_descending_by_similarity(self) -> None:
        query = [0.1] * 384
        results = career_catalog.search(query, top_k=10)
        scores = [score for _career, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_similarity_scores_are_bounded(self) -> None:
        query = [0.1] * 384
        for _career, score in career_catalog.search(query, top_k=10):
            assert 0.0 <= score <= 1.0

    def test_identical_vector_scores_highest_for_itself(self) -> None:
        """
        A career's own embedding, used as the query, should rank that
        exact career first — the most basic sanity check that the
        NumPy cosine-similarity math (replacing FAISS's IndexFlatIP) is
        actually equivalent, not just "runs without crashing".
        """
        matrix = career_catalog._embeddings()
        target_index = 0
        query_vector = matrix[target_index].tolist()

        results = career_catalog.search(query_vector, top_k=1)

        assert results[0][0].onet_code == career_catalog.CAREERS[target_index].onet_code
        assert results[0][1] == pytest.approx(1.0, abs=1e-4)

    def test_embeddings_are_cached_across_calls(self) -> None:
        first = career_catalog._embeddings()
        second = career_catalog._embeddings()
        assert first is second  # same object, not recomputed

    def test_embedding_matrix_shape(self) -> None:
        matrix = career_catalog._embeddings()
        assert matrix.shape == (len(career_catalog.CAREERS), 384)
        # embed_text already L2-normalises every vector (real model path
        # via normalize_embeddings=True, fallback path manually) — each
        # row's own norm should be ~1, which is what makes a plain dot
        # product equivalent to cosine similarity.
        norms = np.linalg.norm(matrix, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-4)
