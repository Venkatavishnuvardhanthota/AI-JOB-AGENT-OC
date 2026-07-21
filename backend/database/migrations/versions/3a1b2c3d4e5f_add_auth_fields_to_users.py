"""add auth fields to users

Revision ID: 3a1b2c3d4e5f
Revises: 880225aef69e
Create Date: 2026-07-21 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3a1b2c3d4e5f"
down_revision: str | None = "880225aef69e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_is_verified", "users", ["is_verified"])
    op.create_index("ix_users_is_admin", "users", ["is_admin"])


def downgrade() -> None:
    op.drop_index("ix_users_is_admin", table_name="users")
    op.drop_index("ix_users_is_verified", table_name="users")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "is_verified")
