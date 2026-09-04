"""add persisted global AI settings table

Revision ID: 1a2b3c4d5e6f
Revises: 9a8b7c6d5e4f
Create Date: 2026-08-01 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1a2b3c4d5e6f"
down_revision: str | None = "9a8b7c6d5e4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("default_provider", sa.String(length=50), nullable=False, server_default="openrouter"),
        sa.Column("default_model", sa.String(length=200), nullable=False, server_default="gpt-4o"),
        sa.Column("fallback_provider", sa.String(length=50), nullable=True),
        sa.Column("fallback_model", sa.String(length=200), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("retry_delay_seconds", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("streaming_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("enabled_providers", sa.Text(), nullable=False, server_default="openrouter"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ai_settings")
