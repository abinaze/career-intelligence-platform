"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-29 15:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── careers ──────────────────────────────────────────────────────────────
    op.create_table(
        "careers",
        sa.Column("onet_code", sa.String(20), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("broad_category", sa.String(200), nullable=False),
        sa.Column("median_salary_usd", sa.Float(), nullable=True),
        sa.Column("outlook_percentile", sa.Float(), nullable=True),
        sa.Column("work_styles", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("skills", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("interests", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("abilities", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("onet_code"),
    )
    op.create_index("ix_careers_onet_code", "careers", ["onet_code"])
    op.create_index("ix_careers_title", "careers", ["title"])
    op.create_index("ix_careers_broad_category", "careers", ["broad_category"])
    op.create_index("ix_careers_broad_category_title", "careers", ["broad_category", "title"])
    op.create_index("ix_careers_id", "careers", ["id"])
    op.create_index("ix_careers_created_at", "careers", ["created_at"])

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("avatar_url", sa.String(2048), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_created_at", "users", ["created_at"])

    # ── user_profiles ─────────────────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("age_range", sa.String(20), nullable=True),
        sa.Column("education_level", sa.String(100), nullable=True),
        sa.Column("current_field", sa.String(200), nullable=True),
        sa.Column("years_of_experience", sa.Integer(), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("primary_goal", sa.String(500), nullable=True),
        sa.Column("career_concerns", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("desired_work_environment", sa.String(200), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
        sa.Column("onboarding_step", sa.Integer(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column("profile_embedding", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"])
    op.create_index("ix_user_profiles_id", "user_profiles", ["id"])
    op.create_index("ix_user_profiles_created_at", "user_profiles", ["created_at"])

    # ── assessment_sessions ───────────────────────────────────────────────────
    op.create_table(
        "assessment_sessions",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assessment_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responses", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_scores", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessment_sessions_user_id", "assessment_sessions", ["user_id"])
    op.create_index(
        "ix_assessment_sessions_assessment_type", "assessment_sessions", ["assessment_type"]
    )
    op.create_index("ix_assessment_sessions_status", "assessment_sessions", ["status"])
    op.create_index("ix_assessment_sessions_id", "assessment_sessions", ["id"])
    op.create_index("ix_assessment_sessions_created_at", "assessment_sessions", ["created_at"])

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    op.create_index("ix_refresh_tokens_created_at", "refresh_tokens", ["created_at"])

    # ── psychometric_scores ───────────────────────────────────────────────────
    op.create_table(
        "psychometric_scores",
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dimension", sa.String(100), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column(
            "assessment_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessment_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("factor_breakdown", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_psychometric_scores_profile_id", "psychometric_scores", ["profile_id"])
    op.create_index("ix_psychometric_scores_dimension", "psychometric_scores", ["dimension"])
    op.create_index("ix_psychometric_scores_id", "psychometric_scores", ["id"])
    op.create_index("ix_psychometric_scores_created_at", "psychometric_scores", ["created_at"])


def downgrade() -> None:
    op.drop_table("psychometric_scores")
    op.drop_table("refresh_tokens")
    op.drop_table("assessment_sessions")
    op.drop_table("user_profiles")
    op.drop_table("users")
    op.drop_table("careers")
