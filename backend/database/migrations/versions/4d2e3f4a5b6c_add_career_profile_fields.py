"""add career profile fields

Revision ID: 4d2e3f4a5b6c
Revises: 3a1b2c3d4e5f
Create Date: 2026-07-21 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "4d2e3f4a5b6c"
down_revision: str | None = "3a1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # CareerProfile new fields
    op.add_column("career_profiles", sa.Column("headline", sa.String(255), nullable=True))
    op.add_column("career_profiles", sa.Column("total_years_experience", sa.Numeric(4, 1), nullable=True))
    op.add_column("career_profiles", sa.Column("current_role", sa.String(255), nullable=True))
    op.add_column("career_profiles", sa.Column("desired_role", sa.String(255), nullable=True))
    op.add_column("career_profiles", sa.Column("employment_status", sa.String(50), nullable=True))
    op.add_column("career_profiles", sa.Column("current_salary", sa.Numeric(12, 2), nullable=True))
    op.add_column("career_profiles", sa.Column("expected_salary", sa.Numeric(12, 2), nullable=True))
    op.add_column("career_profiles", sa.Column("willing_to_relocate", sa.Boolean(), nullable=True))
    op.add_column("career_profiles", sa.Column("visa_sponsorship_requirement", sa.Boolean(), nullable=True))
    op.add_column("career_profiles", sa.Column("notice_period", sa.String(100), nullable=True))
    op.add_column("career_profiles", sa.Column("profile_completeness", sa.Integer(), nullable=True, server_default=sa.text("0")))

    # Education new field
    op.add_column("education", sa.Column("currently_studying", sa.Boolean(), nullable=True, server_default=sa.text("false")))

    # Experience new fields
    op.add_column("experience", sa.Column("responsibilities", JSONB(), nullable=True))
    op.add_column("experience", sa.Column("achievements", JSONB(), nullable=True))
    op.add_column("experience", sa.Column("technologies_used", JSONB(), nullable=True))

    # Skill new fields
    op.add_column("skills", sa.Column("skill_level", sa.String(50), nullable=True))
    op.add_column("skills", sa.Column("display_order", sa.Integer(), nullable=True))

    # Project new fields
    op.add_column("projects", sa.Column("live_url", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("end_date", sa.Date(), nullable=True))

    # SocialLink new table
    op.create_table(
        "social_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_social_links_profile_id", "social_links", ["profile_id"])


def downgrade() -> None:
    # SocialLink
    op.drop_index("ix_social_links_profile_id", table_name="social_links")
    op.drop_table("social_links")

    # Project
    op.drop_column("projects", "end_date")
    op.drop_column("projects", "start_date")
    op.drop_column("projects", "live_url")

    # Skill
    op.drop_column("skills", "display_order")
    op.drop_column("skills", "skill_level")

    # Experience
    op.drop_column("experience", "technologies_used")
    op.drop_column("experience", "achievements")
    op.drop_column("experience", "responsibilities")

    # Education
    op.drop_column("education", "currently_studying")

    # CareerProfile
    op.drop_column("career_profiles", "profile_completeness")
    op.drop_column("career_profiles", "notice_period")
    op.drop_column("career_profiles", "visa_sponsorship_requirement")
    op.drop_column("career_profiles", "willing_to_relocate")
    op.drop_column("career_profiles", "expected_salary")
    op.drop_column("career_profiles", "current_salary")
    op.drop_column("career_profiles", "employment_status")
    op.drop_column("career_profiles", "desired_role")
    op.drop_column("career_profiles", "current_role")
    op.drop_column("career_profiles", "total_years_experience")
    op.drop_column("career_profiles", "headline")
