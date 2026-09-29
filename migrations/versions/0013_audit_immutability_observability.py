"""audit immutability and trace metadata

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("request_id", sa.String(), nullable=True))
    op.add_column("audit_logs", sa.Column("causation_id", sa.String(), nullable=True))
    op.add_column(
        "audit_logs",
        sa.Column(
            "source",
            sa.String(),
            server_default=sa.text("'application'"),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_logs_request", "audit_logs", ["request_id"], unique=False)
    op.create_index(
        "ix_audit_logs_target_occurred",
        "audit_logs",
        ["target_type", "target_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_review_queue_assignee_status",
        "reviewer_queue_items",
        ["assigned_reviewer_id", "status", "entered_queue_at"],
        unique=False,
    )
    op.create_index(
        "ix_handoffs_status_updated",
        "handoffs",
        ["status", "updated_at"],
        unique=False,
    )
    op.execute(
        """
        CREATE FUNCTION careintel_reject_audit_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only'
                USING ERRCODE = '42501';
        END;
        $function$
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION careintel_reject_audit_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS careintel_reject_audit_mutation()")
    op.drop_index("ix_handoffs_status_updated", table_name="handoffs")
    op.drop_index("ix_review_queue_assignee_status", table_name="reviewer_queue_items")
    op.drop_index("ix_audit_logs_target_occurred", table_name="audit_logs")
    op.drop_index("ix_audit_logs_request", table_name="audit_logs")
    op.drop_column("audit_logs", "source")
    op.drop_column("audit_logs", "causation_id")
    op.drop_column("audit_logs", "request_id")
