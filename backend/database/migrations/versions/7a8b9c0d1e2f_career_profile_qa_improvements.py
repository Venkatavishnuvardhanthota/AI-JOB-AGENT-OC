"""career profile QA improvements - v2.1.1

Revision ID: 7a8b9c0d1e2f
Revises: 6f7a8b9c0d1e
Create Date: 2026-07-31 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7a8b9c0d1e2f"
down_revision: str | None = "6f7a8b9c0d1e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # CareerProfile: salary preference (paid_only | paid_preferred | unpaid_acceptable)
    op.add_column("career_profiles", sa.Column("salary_preference", sa.String(50), nullable=True))

    # Education: remove description, add location + cgpa
    op.add_column("education", sa.Column("location", sa.String(255), nullable=True))
    op.add_column("education", sa.Column("cgpa", sa.String(20), nullable=True))
    op.drop_column("education", "description")
    op.drop_column("education", "grade")

    # Achievements table
    op.create_table(
        "achievements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("achievement_type", sa.String(100), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_achievements_profile_id", "achievements", ["profile_id"])
    op.create_index("ix_achievements_title", "achievements", ["title"])

    # Languages: unique (profile_id, language) - dedupe existing rows first
    op.execute(
        """
        DELETE FROM languages a
        USING languages b
        WHERE a.id <> b.id
          AND a.profile_id = b.profile_id
          AND lower(a.language) = lower(b.language)
          AND a.id < b.id
        """
    )
    op.create_unique_constraint("uq_language_profile_language", "languages", ["profile_id", "language"])

    # Social links: unique (profile_id, platform) - dedupe existing rows first
    op.execute(
        """
        DELETE FROM social_links a
        USING social_links b
        WHERE a.id <> b.id
          AND a.profile_id = b.profile_id
          AND lower(a.platform) = lower(b.platform)
          AND a.id < b.id
        """
    )
    op.create_unique_constraint("uq_social_link_profile_platform", "social_links", ["profile_id", "platform"])


def downgrade() -> None:
    op.drop_constraint("uq_social_link_profile_platform", "social_links", type_="unique")
    op.drop_constraint("uq_language_profile_language", "languages", type_="unique")

    op.drop_index("ix_achievements_title", table_name="achievements")
    op.drop_index("ix_achievements_profile_id", table_name="achievements")
    op.drop_table("achievements")

    op.add_column("education", sa.Column("grade", sa.String(50), nullable=True))
    op.add_column("education", sa.Column("description", sa.Text(), nullable=True))
    op.drop_column("education", "cgpa")
    op.drop_column("education", "location")

    op.drop_column("career_profiles", "salary_preference")
