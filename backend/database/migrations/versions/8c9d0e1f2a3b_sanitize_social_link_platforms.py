"""sanitize social link platforms and enforce the allowed set

Revision ID: 8c9d0e1f2a3b
Revises: 7a8b9c0d1e2f
Create Date: 2026-08-01 09:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "8c9d0e1f2a3b"
down_revision: str | None = "7a8b9c0d1e2f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the unique constraint first: legacy cased values (e.g. 'LinkedIn')
    # can collide with already-lowercase rows for the same profile once
    # normalization runs, so dedupe must happen on unconstrained data.
    op.drop_constraint("uq_social_link_profile_platform", "social_links", type_="unique")
    # Normalize legacy platforms (trim, collapse spaces, lowercase) to match
    # the API's normalize_platform() semantics
    op.execute(
        "UPDATE social_links SET platform = lower(replace(trim(platform), ' ', '')) "
        "WHERE platform IS NOT NULL"
    )
    # Coerce unrecognized legacy values (e.g. 'sq') to 'other'
    op.execute(
        "UPDATE social_links SET platform = 'other' "
        "WHERE platform NOT IN ('linkedin', 'github', 'portfolio', 'website', 'other')"
    )
    # Re-dedupe after normalization, since distinct legacy values can collapse
    # onto the same platform for one profile
    op.execute(
        """
        DELETE FROM social_links a
        USING social_links b
        WHERE a.id <> b.id
          AND a.profile_id = b.profile_id
          AND a.platform = b.platform
          AND a.id < b.id
        """
    )
    # Restore uniqueness and add DB-level enforcement of the platform enum
    op.create_unique_constraint(
        "uq_social_link_profile_platform", "social_links", ["profile_id", "platform"]
    )
    op.create_check_constraint(
        "ck_social_link_platform",
        "social_links",
        "platform IN ('linkedin', 'github', 'portfolio', 'website', 'other')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_social_link_platform", "social_links", type_="check")
    op.drop_constraint("uq_social_link_profile_platform", "social_links", type_="unique")
    op.create_unique_constraint(
        "uq_social_link_profile_platform", "social_links", ["profile_id", "platform"]
    )
