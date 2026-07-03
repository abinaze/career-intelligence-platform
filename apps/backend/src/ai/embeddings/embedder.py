"""
Profile and career text embedding using sentence-transformers.

Wraps all-MiniLM-L6-v2 with a lazy-loaded singleton so the 384-d encoder
is initialised once per process. Falls back to a deterministic hash-derived
vector when the model is unavailable (CI / test environments without torch).
"""

from __future__ import annotations

import hashlib
import threading
from typing import Any

import numpy as np

from src.core.config.settings import get_settings
from src.core.logging.setup import get_logger

logger = get_logger(__name__)
_settings = get_settings()

_MODEL_LOCK = threading.Lock()
_model: Any = None


def _load_model() -> Any:
    """Load and cache the sentence-transformer model (thread-safe)."""
    global _model
    if _model is not None:
        return _model
    with _MODEL_LOCK:
        if _model is not None:
            return _model
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import]

            logger.info("Loading embedding model", model=_settings.EMBEDDING_MODEL)
            _model = SentenceTransformer(
                _settings.EMBEDDING_MODEL,
                cache_folder=_settings.MODEL_CACHE_DIR,
            )
            logger.info("Embedding model ready", dim=_settings.EMBEDDING_DIMENSION)
        except Exception as exc:
            logger.warning(
                "sentence-transformers unavailable — using fallback embedder",
                error=str(exc),
            )
            _model = None
    return _model


def _fallback_embedding(text: str) -> list[float]:
    """
    Deterministic unit-normalised 384-d vector derived from SHA-256 of text.
    Consistent across calls but not semantically meaningful; for tests/CI only.
    """
    dim = _settings.EMBEDDING_DIMENSION
    digest = hashlib.sha256(text.encode()).digest()
    raw = np.frombuffer(
        (digest * ((dim // len(digest)) + 1))[:dim], dtype=np.uint8
    ).astype(np.float32)
    raw = raw / 255.0 - 0.5
    norm = np.linalg.norm(raw)
    if norm > 0:
        raw = raw / norm
    return raw.tolist()


def embed_text(text: str) -> list[float]:
    """Encode a single string to a normalised 384-d float vector."""
    if not text or not text.strip():
        return [0.0] * _settings.EMBEDDING_DIMENSION
    model = _load_model()
    if model is None:
        return _fallback_embedding(text)
    vector: np.ndarray = model.encode(
        text, normalize_embeddings=True, show_progress_bar=False
    )
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Encode a list of texts in one efficient batched call."""
    if not texts:
        return []
    model = _load_model()
    if model is None:
        return [_fallback_embedding(t) for t in texts]
    safe = [t if t and t.strip() else " " for t in texts]
    vectors: np.ndarray = model.encode(
        safe,
        batch_size=_settings.EMBEDDING_BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vectors.tolist()


def build_profile_text(
    scores: dict[str, float],
    profile_meta: dict[str, str | None],
) -> str:
    """
    Compose a natural-language summary of a user's psychometric profile
    suitable for semantic embedding and FAISS search.

    Args:
        scores:       dimension name → normalised score (0-100).
        profile_meta: optional biographical fields (education, field, goal).
    """
    parts: list[str] = []
    if education := profile_meta.get("education_level"):
        parts.append(f"Education: {education}.")
    if field := profile_meta.get("current_field"):
        parts.append(f"Current field: {field}.")
    if goal := profile_meta.get("primary_goal"):
        parts.append(f"Career goal: {goal}.")
    if scores:
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_labels = ", ".join(f"{dim} ({score:.0f}/100)" for dim, score in top)
        parts.append(f"Strongest traits: {top_labels}.")
    return " ".join(parts) if parts else "Career profile with no additional details."
