"""add resume strategy fields

Revision ID: 6f7a8b9c0d1e
Revises: 5e6f7a8b9c0d
Create Date: 2026-07-31 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "6f7a8b9c0d1e"
down_revision: str | None = "5e6f7a8b9c0d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ResumeVersion strategy fields
    op.add_column(
        "resume_versions",
        sa.Column("origin", sa.String(20), server_default="master", nullable=False),
    )
    op.add_column(
        "resume_versions",
        sa.Column(
            "parent_resume_id",
            sa.Uuid(),
            sa.ForeignKey("resume_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("resume_versions", sa.Column("generation_metadata", JSONB(), nullable=True))
    op.create_index(
        "ix_resume_versions_user_id_origin", "resume_versions", ["user_id", "origin"]
    )
    op.create_index(
        "ix_resume_versions_user_id_job_origin",
        "resume_versions",
        ["user_id", "generated_for_job_id", "origin"],
    )

    # Application strategy fields
    op.add_column("applications", sa.Column("resume_strategy", sa.String(20), nullable=True))
    op.add_column(
        "applications",
        sa.Column(
            "original_resume_id",
            sa.Uuid(),
            sa.ForeignKey("resume_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "applications",
        sa.Column(
            "generated_resume_id",
            sa.Uuid(),
            sa.ForeignKey("resume_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "applications",
        sa.Column("generated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("tailored", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("applications", sa.Column("generation_timestamp", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_applications_generated_resume_id", "applications", ["generated_resume_id"])
    op.create_index("ix_applications_original_resume_id", "applications", ["original_resume_id"])

    # Per-user AI settings (resume strategy + storage option)
    op.create_table(
        "user_ai_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "resume_strategy",
            sa.String(20),
            server_default="tailor",
            nullable=False,
        ),
        sa.Column(
            "save_generated_resumes",
            sa.String(20),
            server_default="submitted_only",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_ai_settings_user_id"),
    )
    op.create_index("ix_user_ai_settings_user_id", "user_ai_settings", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_ai_settings_user_id", table_name="user_ai_settings")
    op.drop_table("user_ai_settings")

    op.drop_index("ix_applications_original_resume_id", table_name="applications")
    op.drop_index("ix_applications_generated_resume_id", table_name="applications")
    op.drop_column("applications", "generation_timestamp")
    op.drop_column("applications", "tailored")
    op.drop_column("applications", "generated")
    op.drop_column("applications", "generated_resume_id")
    op.drop_column("applications", "original_resume_id")
    op.drop_column("applications", "resume_strategy")

    op.drop_index("ix_resume_versions_user_id_job_origin", table_name="resume_versions")
    op.drop_index("ix_resume_versions_user_id_origin", table_name="resume_versions")
    op.drop_column("resume_versions", "generation_metadata")
    op.drop_column("resume_versions", "parent_resume_id")
    op.drop_column("resume_versions", "origin")
