"""Career occupation model based on O*NET taxonomy."""

from __future__ import annotations

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class Career(Base):
    """
    An occupation drawn from the O*NET taxonomy.

    Stores the structured attributes used by the recommendation engine
    to match careers against a user's psychometric profile.
    """

    __tablename__ = "careers"

    onet_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    broad_category: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    median_salary_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    outlook_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)

    # O*NET structured data stored as JSON arrays/objects
    work_styles: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interests: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    abilities: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Pre-computed embedding for similarity search (stored as JSON float list)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (Index("ix_careers_broad_category_title", "broad_category", "title"),)
