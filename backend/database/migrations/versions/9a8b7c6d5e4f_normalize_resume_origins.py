"""backfill resume origins for uploaded / AI-generated / AI-tailored resumes

Revision ID: 9a8b7c6d5e4f
Revises: 8c9d0e1f2a3b
Create Date: 2026-08-01 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "9a8b7c6d5e4f"
down_revision: str | None = "8c9d0e1f2a3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Optimized / tailored for a job (manual optimize + strategy tailor)
    op.execute(
        "UPDATE resume_versions SET origin = 'ai_tailored' "
        "WHERE resume_type IN ('optimized', 'tailored') OR source = 'optimization'"
    )
    # Generated from the career profile (manual generate + strategy generate),
    # including legacy strategy rows that used origin 'generated'
    op.execute(
        "UPDATE resume_versions SET origin = 'ai_generated' "
        "WHERE resume_type = 'generated' OR origin = 'generated'"
    )
    # Uploaded / imported files (legacy uploads never set source)
    op.execute(
        "UPDATE resume_versions SET origin = 'uploaded' "
        "WHERE source IN ('upload', 'import') "
        "OR change_summary IN ('Uploaded from file', 'Imported resume')"
    )
    # Normalize any NULL/empty origins that slipped through to 'master'
    op.execute(
        "UPDATE resume_versions SET origin = 'master' "
        "WHERE origin IS NULL OR origin = ''"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE resume_versions SET origin = 'generated' "
        "WHERE origin IN ('ai_generated', 'ai_tailored')"
    )
    op.execute("UPDATE resume_versions SET origin = 'master' WHERE origin = 'uploaded'")
