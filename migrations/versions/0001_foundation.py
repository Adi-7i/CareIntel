"""Foundation migration — verifies Alembic pipeline is operational.

This migration intentionally creates no tables.
The CareIntel business schema starts in Step 2.

Revision ID: 0001
Revises:
Create Date: 2026-09-15 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Foundation migration — no schema changes.

    Future steps will add tables via new numbered revisions.
    This revision exists to verify the Alembic pipeline runs end-to-end.
    """
    # Intentionally empty — database schema starts clean in Step 1.
    pass


def downgrade() -> None:
    """Downgrade is a no-op for the empty foundation migration."""
    pass
