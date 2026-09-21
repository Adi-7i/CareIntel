"""structuring

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-21 20:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # structuring_runs
    op.create_table(
        "structuring_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("extraction_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_structuring_runs_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["extraction_run_id"],
            ["extraction_runs.id"],
            name=op.f("fk_structuring_runs_extraction_run_id_extraction_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_structuring_runs")),
        sa.UniqueConstraint("case_id", "extraction_run_id", name="uq_structuring_run_idempotency"),
    )

    # checklist_policy_versions
    op.create_table(
        "checklist_policy_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("version_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checklist_policy_versions")),
        sa.UniqueConstraint("version_key", name=op.f("uq_checklist_policy_versions_version_key")),
    )

    # timeline_events
    op.create_table(
        "timeline_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("structuring_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("source_statement", sa.Text(), nullable=False),
        sa.Column("raw_temporal_expression", sa.Text(), nullable=False),
        sa.Column("temporal_precision", sa.String(), nullable=False),
        sa.Column("resolution_state", sa.String(), nullable=False),
        sa.Column("normalized_start", sa.Date(), nullable=True),
        sa.Column("normalized_end", sa.Date(), nullable=True),
        sa.Column("anchor_description", sa.String(), nullable=True),
        sa.Column("anchor_evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("unresolved_reason", sa.String(), nullable=True),
        sa.Column("ordering_relation", sa.String(), nullable=False),
        sa.Column("ordering_confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("extraction_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["anchor_evidence_id"],
            ["evidence.id"],
            name=op.f("fk_timeline_events_anchor_evidence_id_evidence"),
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["extracted_candidates.id"],
            name=op.f("fk_timeline_events_candidate_id_extracted_candidates"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_timeline_events_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["evidence.id"], name=op.f("fk_timeline_events_evidence_id_evidence")
        ),
        sa.ForeignKeyConstraint(
            ["extraction_run_id"],
            ["extraction_runs.id"],
            name=op.f("fk_timeline_events_extraction_run_id_extraction_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["structuring_run_id"],
            ["structuring_runs.id"],
            name=op.f("fk_timeline_events_structuring_run_id_structuring_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_timeline_events")),
    )
    op.create_index("ix_timeline_event_case", "timeline_events", ["case_id"], unique=False)
    op.create_index("ix_timeline_event_evidence", "timeline_events", ["evidence_id"], unique=False)

    # conflict_records
    op.create_table(
        "conflict_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("detection_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_conflict_records_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["detection_run_id"],
            ["structuring_runs.id"],
            name=op.f("fk_conflict_records_detection_run_id_structuring_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conflict_records")),
    )
    op.create_index(
        "ix_conflict_record_case_field", "conflict_records", ["case_id", "field_type"], unique=False
    )

    # conflict_candidate_links
    op.create_table(
        "conflict_candidate_links",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("conflict_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["extracted_candidates.id"],
            name=op.f("fk_conflict_candidate_links_candidate_id_extracted_candidates"),
        ),
        sa.ForeignKeyConstraint(
            ["conflict_id"],
            ["conflict_records.id"],
            name=op.f("fk_conflict_candidate_links_conflict_id_conflict_records"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conflict_candidate_links")),
        sa.UniqueConstraint("conflict_id", "candidate_id", name="uq_conflict_candidate"),
    )

    # missing_info_items
    op.create_table(
        "missing_info_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_key", sa.String(), nullable=False),
        sa.Column("checklist_version", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("materiality", sa.String(), nullable=False),
        sa.Column("resolution", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_missing_info_items_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"],
            ["structuring_runs.id"],
            name=op.f("fk_missing_info_items_evaluation_run_id_structuring_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_missing_info_items")),
        sa.UniqueConstraint(
            "evaluation_run_id", "requirement_key", name="uq_missing_info_requirement"
        ),
    )

    # clarification_questions
    op.create_table(
        "clarification_questions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_key", sa.String(), nullable=False),
        sa.Column("missing_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("generator_version", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_clarification_questions_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"],
            ["structuring_runs.id"],
            name=op.f("fk_clarification_questions_evaluation_run_id_structuring_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["missing_item_id"],
            ["missing_info_items.id"],
            name=op.f("fk_clarification_questions_missing_item_id_missing_info_items"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clarification_questions")),
        sa.UniqueConstraint("evaluation_run_id", "requirement_key", name="uq_question_requirement"),
    )


def downgrade() -> None:
    op.drop_table("clarification_questions")
    op.drop_table("missing_info_items")
    op.drop_table("conflict_candidate_links")
    op.drop_index("ix_conflict_record_case_field", table_name="conflict_records")
    op.drop_table("conflict_records")
    op.drop_index("ix_timeline_event_evidence", table_name="timeline_events")
    op.drop_index("ix_timeline_event_case", table_name="timeline_events")
    op.drop_table("timeline_events")
    op.drop_table("checklist_policy_versions")
    op.drop_table("structuring_runs")
