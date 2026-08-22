"""
Static career catalog — the portable data bundle Desktop mode reads
instead of the Postgres `careers` table.

This is the single source of truth for the curated O*NET career data.
`src/scripts/load_onet.py` previously defined this same list inline and
wrote it into Postgres for Cloud; now that Cloud is archived
(see docs/NORTH_STAR.md), that role moves to archive/cloud/, and this
module becomes what it always should have been for Desktop: a plain,
importable Python list with no database, no async, and no I/O beyond
computing embeddings once and caching them in memory.

Embeddings are computed lazily on first access via the existing
`embed_text` (which already degrades gracefully without torch/
sentence-transformers — see embedder.py) and cached for the life of
the process, the same lazy-singleton pattern embedder.py itself uses
for the model. This is a deliberately scoped-down interim step short
of docs/NORTH_STAR.md §6 Phase 3's eventual release-time prebuilt
bundle (computing embeddings once at build time and shipping them as
static data, rather than at first request) — that optimisation doesn't
change this module's interface, only how `_embeddings()` is
implemented, so it can be layered on later without touching callers.
"""

from __future__ import annotations

from dataclasses import dataclass
import threading

import numpy as np

from src.ai.embeddings.embedder import embed_text


@dataclass(frozen=True)
class CareerRecord:
    onet_code: str
    title: str
    description: str
    broad_category: str
    median_salary_usd: float | None
    outlook_percentile: float | None
    interests: dict[str, int]


# ── Curated O*NET career catalog ────────────────────────────────────────────
# 10 entries (verified by counting this list directly — an earlier
# planning document stated 14, which was wrong; corrected here and in
# the docs that cited it). Each follows the O*NET taxonomy with RIASEC
# interest weights (0-100). Extracted verbatim from the data previously
# inlined in src/scripts/load_onet.py's ONET_CAREERS list.
CAREERS: list[CareerRecord] = [
    CareerRecord(
        onet_code="15-1252.00",
        title="Software Developers",
        description=(
            "Research, design, and develop computer and network software or specialised "
            "utility programs. Analyse user needs and develop software solutions."
        ),
        broad_category="Computer and Mathematical",
        median_salary_usd=124_200.0,
        outlook_percentile=88.0,
        interests={
            "Realistic": 40,
            "Investigative": 85,
            "Artistic": 35,
            "Social": 20,
            "Enterprising": 30,
            "Conventional": 55,
        },
    ),
    CareerRecord(
        onet_code="29-1141.00",
        title="Registered Nurses",
        description=(
            "Assess patient health problems and needs, develop and implement nursing care "
            "plans, and maintain medical records. Administer nursing care to ill, injured, "
            "or disabled patients."
        ),
        broad_category="Healthcare Practitioners and Technical",
        median_salary_usd=81_220.0,
        outlook_percentile=80.0,
        interests={
            "Realistic": 45,
            "Investigative": 55,
            "Artistic": 20,
            "Social": 90,
            "Enterprising": 35,
            "Conventional": 50,
        },
    ),
    CareerRecord(
        onet_code="11-1021.00",
        title="General and Operations Managers",
        description=(
            "Plan, direct, or coordinate the operations of public or private sector "
            "organisations. Duties include formulating policies, managing daily operations, "
            "and planning the use of materials and human resources."
        ),
        broad_category="Management",
        median_salary_usd=103_650.0,
        outlook_percentile=65.0,
        interests={
            "Realistic": 30,
            "Investigative": 45,
            "Artistic": 20,
            "Social": 55,
            "Enterprising": 90,
            "Conventional": 70,
        },
    ),
    CareerRecord(
        onet_code="25-2021.00",
        title="Elementary School Teachers",
        description=(
            "Teach academic and social skills to students in Kindergarten through Grade 6. "
            "Adapt teaching methods to meet students' varying needs and interests."
        ),
        broad_category="Education, Training, and Library",
        median_salary_usd=61_400.0,
        outlook_percentile=55.0,
        interests={
            "Realistic": 25,
            "Investigative": 35,
            "Artistic": 50,
            "Social": 95,
            "Enterprising": 40,
            "Conventional": 45,
        },
    ),
    CareerRecord(
        onet_code="17-2051.00",
        title="Civil Engineers",
        description=(
            "Perform engineering duties in planning, designing, and overseeing construction "
            "and maintenance of building structures and facilities."
        ),
        broad_category="Architecture and Engineering",
        median_salary_usd=95_890.0,
        outlook_percentile=70.0,
        interests={
            "Realistic": 85,
            "Investigative": 75,
            "Artistic": 30,
            "Social": 30,
            "Enterprising": 45,
            "Conventional": 65,
        },
    ),
    CareerRecord(
        onet_code="27-1024.00",
        title="Graphic Designers",
        description=(
            "Design or create graphics to meet specific commercial or promotional needs, "
            "such as packaging, displays, or logos. May use a variety of mediums to achieve "
            "artistic or decorative effects."
        ),
        broad_category="Arts, Design, Entertainment, Sports, and Media",
        median_salary_usd=57_990.0,
        outlook_percentile=42.0,
        interests={
            "Realistic": 35,
            "Investigative": 30,
            "Artistic": 95,
            "Social": 40,
            "Enterprising": 45,
            "Conventional": 55,
        },
    ),
    CareerRecord(
        onet_code="13-2011.00",
        title="Accountants and Auditors",
        description=(
            "Examine, analyse, and interpret accounting records to prepare financial "
            "statements, give advice, or audit and evaluate statements prepared by others."
        ),
        broad_category="Business and Financial Operations",
        median_salary_usd=78_000.0,
        outlook_percentile=58.0,
        interests={
            "Realistic": 30,
            "Investigative": 55,
            "Artistic": 15,
            "Social": 30,
            "Enterprising": 50,
            "Conventional": 90,
        },
    ),
    CareerRecord(
        onet_code="19-1042.00",
        title="Medical Scientists",
        description=(
            "Conduct research dealing with the understanding of human diseases and the "
            "improvement of human health. Engage in clinical investigation or other research."
        ),
        broad_category="Life, Physical, and Social Science",
        median_salary_usd=99_930.0,
        outlook_percentile=82.0,
        interests={
            "Realistic": 45,
            "Investigative": 95,
            "Artistic": 35,
            "Social": 40,
            "Enterprising": 30,
            "Conventional": 50,
        },
    ),
    CareerRecord(
        onet_code="41-3031.00",
        title="Securities, Commodities, and Financial Services Sales Agents",
        description=(
            "Buy and sell securities or commodities in investment and trading firms, "
            "or provide financial services to businesses and individuals."
        ),
        broad_category="Sales and Related",
        median_salary_usd=98_600.0,
        outlook_percentile=60.0,
        interests={
            "Realistic": 20,
            "Investigative": 50,
            "Artistic": 20,
            "Social": 55,
            "Enterprising": 90,
            "Conventional": 60,
        },
    ),
    CareerRecord(
        onet_code="21-1014.00",
        title="Mental Health Counselors",
        description=(
            "Counsel with emphasis on prevention. Work with individuals and groups to promote "
            "optimum mental and emotional health. May help individuals deal with addictions "
            "and substance abuse, family problems, or personal issues."
        ),
        broad_category="Community and Social Service",
        median_salary_usd=51_340.0,
        outlook_percentile=85.0,
        interests={
            "Realistic": 20,
            "Investigative": 50,
            "Artistic": 35,
            "Social": 95,
            "Enterprising": 40,
            "Conventional": 30,
        },
    ),
]


_embedding_lock = threading.Lock()
_embedding_matrix: np.ndarray | None = None


def _embeddings() -> np.ndarray:
    """
    Return an (N, EMBEDDING_DIMENSION) matrix of L2-normalised career
    embeddings, one row per CAREERS entry in order, computed once and
    cached for the life of the process.
    """
    global _embedding_matrix
    if _embedding_matrix is not None:
        return _embedding_matrix
    with _embedding_lock:
        if _embedding_matrix is not None:
            return _embedding_matrix
        vectors = [
            embed_text(f"{c.title}. {c.description} Category: {c.broad_category}.") for c in CAREERS
        ]
        _embedding_matrix = np.array(vectors, dtype=np.float32)
    return _embedding_matrix


def search(query_vector: list[float], top_k: int = 20) -> list[tuple[CareerRecord, float]]:
    """
    Return the top-k careers most similar to `query_vector`, as
    (career, similarity_score) pairs sorted by descending similarity.

    Plain NumPy dot product, not FAISS — both `embed_text`'s real
    model path and its fallback path already return L2-normalised
    vectors, so a dot product against this catalog's own normalised
    embeddings *is* cosine similarity, exactly the same math FAISS's
    IndexFlatIP did. FAISS added real value at a much larger catalog
    scale; at 10 entries it added a native, cross-platform-fragile
    dependency for a problem NumPy already solves in well under a
    millisecond. See docs/desktop/TRANSFORMATION_PLAN.md section 5 for
    the original reasoning.
    """
    if not CAREERS:
        return []
    matrix = _embeddings()
    query = np.asarray(query_vector, dtype=np.float32)
    similarities = matrix @ query
    k = min(top_k, len(CAREERS))
    top_indices = np.argsort(-similarities)[:k]
    return [(CAREERS[i], float(np.clip(similarities[i], 0.0, 1.0))) for i in top_indices]
