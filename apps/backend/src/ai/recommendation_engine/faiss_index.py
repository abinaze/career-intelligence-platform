"""
FAISS index for career similarity search.

Maintains an in-memory IndexFlatIP (inner-product / cosine similarity) index
over all career embeddings. All vectors are L2-normalised before insertion
so inner-product search is equivalent to cosine similarity.

The module exposes a process-level singleton ``career_index`` that is built
once on startup (or on demand) and queried per request.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Any

import numpy as np

from src.core.config.settings import get_settings
from src.core.logging.setup import get_logger

logger = get_logger(__name__)
_settings = get_settings()


@dataclass
class CareerIndexEntry:
    """Maps a FAISS slot position back to a career DB record."""

    faiss_idx: int
    onet_code: str
    career_id: str
    title: str


@dataclass
class SimilarityResult:
    """A single nearest-neighbour hit from the FAISS index."""

    onet_code: str
    career_id: str
    title: str
    similarity_score: float


class CareerFaissIndex:
    """
    Thread-safe FAISS flat inner-product index over career embeddings.

    Usage::

        career_index.build(careers)          # list[dict] with 'embedding' key
        results = career_index.search(vec, top_k=10)
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._index: Any = None
        self._entries: list[CareerIndexEntry] = []
        self._dim: int = _settings.EMBEDDING_DIMENSION

    # ── Build ──────────────────────────────────────────────────────────────

    def build(self, careers: list[dict]) -> None:
        """
        (Re)build the index from a list of career dicts.

        Each dict must contain: ``id``, ``onet_code``, ``title``,
        ``embedding`` (list[float] of length EMBEDDING_DIMENSION).
        Careers without a valid embedding are silently skipped.
        """
        try:
            import faiss  # type: ignore[import]
        except ImportError:
            logger.warning("faiss-cpu not installed — similarity search unavailable")
            return

        vectors: list[list[float]] = []
        entries: list[CareerIndexEntry] = []

        for career in careers:
            emb = career.get("embedding")
            if not emb or len(emb) != self._dim:
                continue
            entries.append(
                CareerIndexEntry(
                    faiss_idx=len(vectors),
                    onet_code=career["onet_code"],
                    career_id=str(career["id"]),
                    title=career["title"],
                )
            )
            vectors.append(emb)

        if not vectors:
            logger.warning("No careers with valid embeddings — FAISS index is empty")
            return

        matrix = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(matrix)

        index = faiss.IndexFlatIP(self._dim)
        index.add(matrix)  # type: ignore[arg-type]

        with self._lock:
            self._index = index
            self._entries = entries

        logger.info("FAISS career index built", career_count=len(entries))

    # ── Search ─────────────────────────────────────────────────────────────

    def search(self, query_vector: list[float], top_k: int = 20) -> list[SimilarityResult]:
        """
        Return the top-k most similar careers for a query embedding.

        The query vector is normalised before search so raw or
        pre-normalised inputs both work correctly.
        Returns an empty list if the index has not been built yet.
        """
        with self._lock:
            if self._index is None or not self._entries:
                return []
            try:
                import faiss  # type: ignore[import]

                q = np.array([query_vector], dtype=np.float32)
                faiss.normalize_L2(q)
                k = min(top_k, len(self._entries))
                distances, indices = self._index.search(q, k)

                results: list[SimilarityResult] = []
                for dist, idx in zip(distances[0], indices[0], strict=False):
                    if idx < 0 or idx >= len(self._entries):
                        continue
                    entry = self._entries[idx]
                    results.append(
                        SimilarityResult(
                            onet_code=entry.onet_code,
                            career_id=entry.career_id,
                            title=entry.title,
                            similarity_score=float(np.clip(dist, 0.0, 1.0)),
                        )
                    )
                return results
            except Exception as exc:
                logger.error("FAISS search failed", error=str(exc))
                return []

    # ── Persistence ────────────────────────────────────────────────────────

    def save(self, path: str | None = None) -> None:
        """Persist the index to disk for fast reload on restart."""
        try:
            import faiss  # type: ignore[import]

            index_path = Path(path or _settings.FAISS_INDEX_PATH)
            index_path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                if self._index is None:
                    return
                faiss.write_index(self._index, str(index_path))
            logger.info("FAISS index saved", path=str(index_path))
        except Exception as exc:
            logger.error("Failed to save FAISS index", error=str(exc))

    def load(self, path: str | None = None) -> bool:
        """Load a previously saved index from disk. Returns True on success."""
        try:
            import faiss  # type: ignore[import]

            index_path = Path(path or _settings.FAISS_INDEX_PATH)
            if not index_path.exists():
                return False
            index = faiss.read_index(str(index_path))
            with self._lock:
                self._index = index
            logger.info("FAISS index loaded from disk", path=str(index_path))
            return True
        except Exception as exc:
            logger.warning("Could not load FAISS index", error=str(exc))
            return False

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)

    @property
    def is_ready(self) -> bool:
        with self._lock:
            return self._index is not None and len(self._entries) > 0


# ── Process-level singleton ────────────────────────────────────────────────
career_index = CareerFaissIndex()
