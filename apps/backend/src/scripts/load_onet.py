"""
O*NET career data loader.

Seeds the careers table with a curated set of O*NET occupations,
computes embeddings for each, and builds the FAISS index.

Usage::

    uv run python -m src.scripts.load_onet

or via the Makefile target::

    make load-onet
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.ai.embeddings.embedder import embed_text
from src.ai.recommendation_engine.faiss_index import career_index
from src.core.config.settings import get_settings
from src.core.logging.setup import configure_logging, get_logger
from src.db.models.career import Career

configure_logging()
logger = get_logger(__name__)
_settings = get_settings()

# ── Curated O*NET career seed data ────────────────────────────────────────────
# Each entry follows the O*NET taxonomy with RIASEC interest weights (0-100).
ONET_CAREERS: list[dict] = [
    {
        "onet_code": "15-1252.00",
        "title": "Software Developers",
        "description": (
            "Research, design, and develop computer and network software or specialised "
            "utility programs. Analyse user needs and develop software solutions."
        ),
        "broad_category": "Computer and Mathematical",
        "median_salary_usd": 124_200.0,
        "outlook_percentile": 88.0,
        "interests": {
            "Realistic": 40,
            "Investigative": 85,
            "Artistic": 35,
            "Social": 20,
            "Enterprising": 30,
            "Conventional": 55,
        },
    },
    {
        "onet_code": "29-1141.00",
        "title": "Registered Nurses",
        "description": (
            "Assess patient health problems and needs, develop and implement nursing care plans, "
            "and maintain medical records. Administer nursing care to ill, injured, "
            "or disabled patients."
        ),
        "broad_category": "Healthcare Practitioners and Technical",
        "median_salary_usd": 81_220.0,
        "outlook_percentile": 80.0,
        "interests": {
            "Realistic": 45,
            "Investigative": 55,
            "Artistic": 20,
            "Social": 90,
            "Enterprising": 35,
            "Conventional": 50,
        },
    },
    {
        "onet_code": "11-1021.00",
        "title": "General and Operations Managers",
        "description": (
            "Plan, direct, or coordinate the operations of public or private sector organisations. "
            "Duties include formulating policies, managing daily operations, "
            "and planning the use of "
            "materials and human resources."
        ),
        "broad_category": "Management",
        "median_salary_usd": 103_650.0,
        "outlook_percentile": 65.0,
        "interests": {
            "Realistic": 30,
            "Investigative": 45,
            "Artistic": 20,
            "Social": 55,
            "Enterprising": 90,
            "Conventional": 70,
        },
    },
    {
        "onet_code": "25-2021.00",
        "title": "Elementary School Teachers",
        "description": (
            "Teach academic and social skills to students in Kindergarten through Grade 6. "
            "Adapt teaching methods to meet students' varying needs and interests."
        ),
        "broad_category": "Education, Training, and Library",
        "median_salary_usd": 61_400.0,
        "outlook_percentile": 55.0,
        "interests": {
            "Realistic": 25,
            "Investigative": 35,
            "Artistic": 50,
            "Social": 95,
            "Enterprising": 40,
            "Conventional": 45,
        },
    },
    {
        "onet_code": "17-2051.00",
        "title": "Civil Engineers",
        "description": (
            "Perform engineering duties in planning, designing, and overseeing construction "
            "and maintenance of building structures and facilities."
        ),
        "broad_category": "Architecture and Engineering",
        "median_salary_usd": 95_890.0,
        "outlook_percentile": 70.0,
        "interests": {
            "Realistic": 85,
            "Investigative": 75,
            "Artistic": 30,
            "Social": 30,
            "Enterprising": 45,
            "Conventional": 65,
        },
    },
    {
        "onet_code": "27-1024.00",
        "title": "Graphic Designers",
        "description": (
            "Design or create graphics to meet specific commercial or promotional needs, "
            "such as packaging, displays, or logos. May use a variety of mediums to achieve "
            "artistic or decorative effects."
        ),
        "broad_category": "Arts, Design, Entertainment, Sports, and Media",
        "median_salary_usd": 57_990.0,
        "outlook_percentile": 42.0,
        "interests": {
            "Realistic": 35,
            "Investigative": 30,
            "Artistic": 95,
            "Social": 40,
            "Enterprising": 45,
            "Conventional": 55,
        },
    },
    {
        "onet_code": "13-2011.00",
        "title": "Accountants and Auditors",
        "description": (
            "Examine, analyse, and interpret accounting records to prepare financial statements, "
            "give advice, or audit and evaluate statements prepared by others."
        ),
        "broad_category": "Business and Financial Operations",
        "median_salary_usd": 78_000.0,
        "outlook_percentile": 58.0,
        "interests": {
            "Realistic": 30,
            "Investigative": 55,
            "Artistic": 15,
            "Social": 30,
            "Enterprising": 50,
            "Conventional": 90,
        },
    },
    {
        "onet_code": "19-1042.00",
        "title": "Medical Scientists",
        "description": (
            "Conduct research dealing with the understanding of human diseases and the "
            "improvement of human health. Engage in clinical investigation or other research."
        ),
        "broad_category": "Life, Physical, and Social Science",
        "median_salary_usd": 99_930.0,
        "outlook_percentile": 82.0,
        "interests": {
            "Realistic": 45,
            "Investigative": 95,
            "Artistic": 35,
            "Social": 40,
            "Enterprising": 30,
            "Conventional": 50,
        },
    },
    {
        "onet_code": "41-3031.00",
        "title": "Securities, Commodities, and Financial Services Sales Agents",
        "description": (
            "Buy and sell securities or commodities in investment and trading firms, "
            "or provide financial services to businesses and individuals."
        ),
        "broad_category": "Sales and Related",
        "median_salary_usd": 98_600.0,
        "outlook_percentile": 60.0,
        "interests": {
            "Realistic": 20,
            "Investigative": 50,
            "Artistic": 20,
            "Social": 55,
            "Enterprising": 90,
            "Conventional": 60,
        },
    },
    {
        "onet_code": "21-1014.00",
        "title": "Mental Health Counselors",
        "description": (
            "Counsel with emphasis on prevention. Work with individuals and groups to promote "
            "optimum mental and emotional health. May help individuals deal with addictions "
            "and substance abuse, family problems, or personal issues."
        ),
        "broad_category": "Community and Social Service",
        "median_salary_usd": 51_340.0,
        "outlook_percentile": 85.0,
        "interests": {
            "Realistic": 20,
            "Investigative": 50,
            "Artistic": 35,
            "Social": 95,
            "Enterprising": 40,
            "Conventional": 30,
        },
    },
]


async def load_careers(session: AsyncSession) -> int:
    """Insert or skip careers in the seed list. Returns count of new records inserted."""
    inserted = 0
    for data in ONET_CAREERS:
        existing_result = await session.execute(
            select(Career).where(Career.onet_code == data["onet_code"])
        )
        if existing_result.scalar_one_or_none():
            logger.info("Skipping existing career", onet_code=data["onet_code"])
            continue

        # Build a description string for embedding
        embed_text_str = (
            f"{data['title']}. {data['description']} Category: {data['broad_category']}."
        )
        embedding = embed_text(embed_text_str)

        career = Career(
            id=uuid.uuid4(),
            onet_code=data["onet_code"],
            title=data["title"],
            description=data["description"],
            broad_category=data["broad_category"],
            median_salary_usd=data.get("median_salary_usd"),
            outlook_percentile=data.get("outlook_percentile"),
            interests=data.get("interests"),
            embedding=embedding,
        )
        session.add(career)
        inserted += 1
        logger.info("Inserted career", title=data["title"])

    await session.commit()
    return inserted


async def build_faiss_from_db(session: AsyncSession) -> None:
    """Load all careers with embeddings from DB and rebuild the FAISS index."""
    result = await session.execute(select(Career))
    careers = list(result.scalars().all())
    career_dicts = [
        {
            "id": str(c.id),
            "onet_code": c.onet_code,
            "title": c.title,
            "embedding": c.embedding,
        }
        for c in careers
        if c.embedding
    ]
    career_index.build(career_dicts)
    career_index.save()
    logger.info("FAISS index built and saved", career_count=len(career_dicts))


async def main() -> None:
    engine = create_async_engine(_settings.DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        logger.info("Loading O*NET careers into database...")
        inserted = await load_careers(session)
        logger.info("Careers loaded", inserted=inserted)

        logger.info("Building FAISS index from database...")
        await build_faiss_from_db(session)

    await engine.dispose()
    logger.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
