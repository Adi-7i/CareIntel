"""attach explicit administrative permissions to the admin role

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-30 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # These are the only permissions explicitly classified as Admin in the
    # existing Permission enum. Clinical permissions remain separately mapped.
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles AS r
        CROSS JOIN permissions AS p
        WHERE r.name = 'admin'
          AND p.code IN ('manage:users', 'manage:system')
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM role_permissions AS rp
        USING roles AS r, permissions AS p
        WHERE rp.role_id = r.id
          AND rp.permission_id = p.id
          AND r.name = 'admin'
          AND p.code IN ('manage:users', 'manage:system')
        """
    )
