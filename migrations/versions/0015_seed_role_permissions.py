"""seed missing domain permissions and establish clinical role permissions

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-02 14:35:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ALL_PERMISSIONS = [
    "manage:users",
    "manage:system",
    "consent:read",
    "consent:write",
    "case:read",
    "case:write",
    "evidence:read",
    "evidence:write",
    "processing:read",
    "processing:write",
    "structuring:read",
    "structuring:write",
    "knowledge:read",
    "knowledge:write",
    "ai:read",
    "ai:write",
    "review:read",
    "review:write",
    "review:assign",
    "escalation:read",
    "escalation:write",
    "referral:read",
    "referral:write",
    "handoff:read",
    "handoff:write",
    "recipient:manage",
]

DOCTOR_PERMISSIONS = [
    "consent:read",
    "consent:write",
    "case:read",
    "case:write",
    "evidence:read",
    "evidence:write",
    "processing:read",
    "processing:write",
    "structuring:read",
    "structuring:write",
    "knowledge:read",
    "knowledge:write",
    "ai:read",
    "ai:write",
    "review:read",
    "review:write",
    "review:assign",
    "escalation:read",
    "escalation:write",
    "referral:read",
    "referral:write",
    "handoff:read",
    "handoff:write",
]

NURSE_PERMISSIONS = [
    "consent:read",
    "consent:write",
    "case:read",
    "case:write",
    "evidence:read",
    "evidence:write",
    "processing:read",
    "structuring:read",
    "review:read",
    "review:write",
    "knowledge:read",
]

HEALTH_WORKER_PERMISSIONS = [
    "consent:read",
    "consent:write",
    "case:read",
    "case:write",
    "evidence:read",
    "evidence:write",
    "processing:read",
    "structuring:read",
    "review:write",
]

REVIEWER_PERMISSIONS = [
    "case:read",
    "evidence:read",
    "processing:read",
    "structuring:read",
    "ai:read",
    "review:read",
    "review:write",
    "escalation:read",
    "escalation:write",
]


def upgrade() -> None:
    # 1. Insert any missing permissions into the permissions table
    for perm in ALL_PERMISSIONS:
        op.execute(
            f"""
            INSERT INTO permissions (code)
            VALUES ('{perm}')
            ON CONFLICT (code) DO NOTHING
            """
        )

    # 2. Assign Doctor & Medical Officer permissions
    doc_perms_sql = "', '".join(DOCTOR_PERMISSIONS)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles AS r
        CROSS JOIN permissions AS p
        WHERE r.name IN ('doctor', 'medical_officer')
          AND p.code IN ('{doc_perms_sql}')
        ON CONFLICT DO NOTHING
        """
    )

    # 3. Assign Nurse permissions
    nurse_perms_sql = "', '".join(NURSE_PERMISSIONS)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles AS r
        CROSS JOIN permissions AS p
        WHERE r.name = 'nurse'
          AND p.code IN ('{nurse_perms_sql}')
        ON CONFLICT DO NOTHING
        """
    )

    # 4. Assign Health Worker (CHO) permissions
    cho_perms_sql = "', '".join(HEALTH_WORKER_PERMISSIONS)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles AS r
        CROSS JOIN permissions AS p
        WHERE r.name = 'health_worker'
          AND p.code IN ('{cho_perms_sql}')
        ON CONFLICT DO NOTHING
        """
    )

    # 5. Assign Reviewer permissions
    reviewer_perms_sql = "', '".join(REVIEWER_PERMISSIONS)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles AS r
        CROSS JOIN permissions AS p
        WHERE r.name = 'reviewer'
          AND p.code IN ('{reviewer_perms_sql}')
        ON CONFLICT DO NOTHING
        """
    )

    # 6. Assign All permissions to Admin
    all_perms_sql = "', '".join(ALL_PERMISSIONS)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles AS r
        CROSS JOIN permissions AS p
        WHERE r.name = 'admin'
          AND p.code IN ('{all_perms_sql}')
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    # Remove newly assigned permissions for non-admin roles
    op.execute(
        """
        DELETE FROM role_permissions AS rp
        USING roles AS r, permissions AS p
        WHERE rp.role_id = r.id
          AND rp.permission_id = p.id
          AND r.name IN ('doctor', 'medical_officer', 'nurse', 'health_worker', 'reviewer')
          AND p.code NOT IN (
              'case:read', 'case:write', 'evidence:read', 'evidence:write',
              'processing:read', 'processing:write'
          )
        """
    )
