"""async dispatch and human review recovery

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-26 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _add_dispatch_columns(table: str) -> None:
    op.add_column(
        table,
        sa.Column(
            "dispatch_status",
            sa.String(),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
    )
    op.add_column(
        table,
        sa.Column("dispatch_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        table,
        sa.Column(
            "max_dispatch_attempts", sa.Integer(), server_default=sa.text("8"), nullable=False
        ),
    )
    op.add_column(table, sa.Column("next_attempt_at", sa.DateTime(), nullable=True))
    op.add_column(table, sa.Column("claimed_at", sa.DateTime(), nullable=True))
    op.add_column(table, sa.Column("claimed_by", sa.String(), nullable=True))
    op.add_column(table, sa.Column("last_error_category", sa.String(), nullable=True))
    op.add_column(table, sa.Column("celery_task_id", sa.String(), nullable=True))
    op.create_index(
        f"ix_{table}_dispatch_eligible",
        table,
        ["dispatch_status", "next_attempt_at", "occurred_at"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )


def _drop_dispatch_columns(table: str) -> None:
    op.drop_index(f"ix_{table}_dispatch_eligible", table_name=table)
    for column in (
        "celery_task_id",
        "last_error_category",
        "claimed_by",
        "claimed_at",
        "next_attempt_at",
        "max_dispatch_attempts",
        "dispatch_attempts",
        "dispatch_status",
    ):
        op.drop_column(table, column)


def upgrade() -> None:
    _add_dispatch_columns("case_outbox")
    _add_dispatch_columns("evidence_outbox")

    op.add_column(
        "ai_drafts",
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )
    op.add_column(
        "reviewer_queue_items",
        sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_reviewer_queue_items_encounter_id_encounters",
        "reviewer_queue_items",
        "encounters",
        ["encounter_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "review_decisions",
        sa.Column("draft_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("review_decisions", sa.Column("draft_version", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_review_decisions_draft_id_ai_drafts",
        "review_decisions",
        "ai_drafts",
        ["draft_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_review_decisions_case_version", "review_decisions", ["case_id", "case_version"]
    )

    op.drop_constraint("uq_reviewer_notes_active", "reviewer_notes", type_="unique")
    op.create_index(
        "uq_reviewer_notes_active",
        "reviewer_notes",
        ["case_id"],
        unique=True,
        postgresql_where=sa.text("superseded_by IS NULL"),
    )
    op.create_index(
        "uq_escalation_records_open_case",
        "escalation_records",
        ["case_id"],
        unique=True,
        postgresql_where=sa.text("status = 'OPEN'"),
    )

    op.add_column("handoffs", sa.Column("channel", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("handoffs", "channel")
    op.drop_index("uq_escalation_records_open_case", table_name="escalation_records")
    op.drop_index("uq_reviewer_notes_active", table_name="reviewer_notes")
    op.create_unique_constraint("uq_reviewer_notes_active", "reviewer_notes", ["case_id"])
    op.drop_constraint("uq_review_decisions_case_version", "review_decisions", type_="unique")
    op.drop_constraint(
        "fk_review_decisions_draft_id_ai_drafts", "review_decisions", type_="foreignkey"
    )
    op.drop_column("review_decisions", "draft_version")
    op.drop_column("review_decisions", "draft_id")
    op.drop_constraint(
        "fk_reviewer_queue_items_encounter_id_encounters",
        "reviewer_queue_items",
        type_="foreignkey",
    )
    op.drop_column("reviewer_queue_items", "encounter_id")
    op.drop_column("ai_drafts", "version")
    _drop_dispatch_columns("evidence_outbox")
    _drop_dispatch_columns("case_outbox")
