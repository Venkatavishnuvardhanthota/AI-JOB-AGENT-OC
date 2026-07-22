"""add resume sections and version fields

Revision ID: 5e6f7a8b9c0d
Revises: 4d2e3f4a5b6c
Create Date: 2026-07-22 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "5e6f7a8b9c0d"
down_revision: str | None = "4d2e3f4a5b6c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ResumeVersion new fields
    op.add_column("resume_versions", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("resume_versions", sa.Column("status", sa.String(20), server_default="draft", nullable=False))
    op.add_column("resume_versions", sa.Column("source", sa.String(20), server_default="manual", nullable=False))
    op.add_column("resume_versions", sa.Column("resume_type", sa.String(50), nullable=True))
    op.add_column(
        "resume_versions", sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False)
    )
    op.add_column("resume_versions", sa.Column("change_summary", sa.Text(), nullable=True))
    op.add_column(
        "resume_versions",
        sa.Column(
            "previous_version_id",
            sa.Uuid(),
            sa.ForeignKey("resume_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_resume_versions_user_id_default", "resume_versions", ["user_id", "is_default"])
    op.create_index("ix_resume_versions_status", "resume_versions", ["status"])

    # ResumeSection new table
    op.create_table(
        "resume_sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("section_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("content", JSONB(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("visible", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resume_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_sections_resume_id", "resume_sections", ["resume_id"])
    op.create_index(
        "ix_resume_sections_resume_id_order", "resume_sections", ["resume_id", "sort_order"]
    )


def downgrade() -> None:
    # ResumeSection
    op.drop_index("ix_resume_sections_resume_id_order", table_name="resume_sections")
    op.drop_index("ix_resume_sections_resume_id", table_name="resume_sections")
    op.drop_table("resume_sections")

    # ResumeVersion
    op.drop_index("ix_resume_versions_status", table_name="resume_versions")
    op.drop_index("ix_resume_versions_user_id_default", table_name="resume_versions")
    op.drop_column("resume_versions", "previous_version_id")
    op.drop_column("resume_versions", "change_summary")
    op.drop_column("resume_versions", "is_default")
    op.drop_column("resume_versions", "resume_type")
    op.drop_column("resume_versions", "source")
    op.drop_column("resume_versions", "status")
    op.drop_column("resume_versions", "description")
