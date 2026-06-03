"""User profile and psychometric data models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class UserProfile(Base):
    """
    Extended user profile with biographical and preference data.
    Distinct from User to keep the authentication model clean.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    age_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_field: Mapped[str | None] = mapped_column(String(200), nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    primary_goal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    career_concerns: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    desired_work_environment: Mapped[str | None] = mapped_column(String(200), nullable=True)

    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    completeness_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    profile_embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    embedding_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="profile",
    )

    psychometric_scores: Mapped[list["PsychometricScore"]] = relationship(
        "PsychometricScore",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="select",
    )


class AssessmentSession(Base):
    """A single psychometric assessment session."""

    __tablename__ = "assessment_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assessment_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="in_progress",
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    responses: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="assessment_sessions",
    )


class PsychometricScore(Base):
    """
    Computed psychometric dimension scores for a user profile.
    Each row represents one dimension.
    """

    __tablename__ = "psychometric_scores"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dimension: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    assessment_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )

    factor_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="psychometric_scores",
    )
