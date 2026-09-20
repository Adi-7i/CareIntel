"""
case_management

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-20 10:40:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. cases table
    op.create_table(
        "cases",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("synthetic_subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("opened_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cases")),
        sa.ForeignKeyConstraint(
            ["opened_by"],
            ["users.id"],
            name=op.f("fk_cases_opened_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to"],
            ["users.id"],
            name=op.f("fk_cases_assigned_to_users"),
        ),
    )
    op.create_index(
        "ix_cases_synthetic_subject",
        "cases",
        ["synthetic_subject_id"],
        unique=False,
    )
    op.create_index(
        "ix_cases_facility_state",
        "cases",
        ["facility_id", "state"],
        unique=False,
    )

    # 2. encounters table
    op.create_table(
        "encounters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("encounter_type", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_encounters")),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_encounters_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_encounters_created_by_users"),
        ),
    )
    op.create_index(
        "ix_encounters_case_occurred",
        "encounters",
        ["case_id", "occurred_at"],
        unique=False,
    )

    # 3. case_state_history table
    op.create_table(
        "case_state_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_state", sa.String(), nullable=False),
        sa.Column("to_state", sa.String(), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column(
            "transitioned_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("command_type", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_state_history")),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_case_state_history_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_case_state_history_actor_id_users"),
        ),
    )
    op.create_index(
        "ix_case_history_case_version",
        "case_state_history",
        ["case_id", "aggregate_version"],
        unique=True,
    )

    # 4. case_outbox table
    op.create_table(
        "case_outbox",
        sa.Column("id", sa.String(), nullable=False, comment="ULID as primary key"),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("producer", sa.String(), nullable=False),
        sa.Column("correlation_id", sa.String(), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_outbox")),
    )
    op.create_index(
        "ix_case_outbox_unpublished",
        "case_outbox",
        ["id"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )

    # Seed case_read and case_write to doctor and medical_officer and reviewer
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE r.name IN ('doctor', 'medical_officer', 'reviewer', 'admin')
          AND p.code IN ('case:read', 'case:write')
        ON CONFLICT DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_case_outbox_unpublished",
        table_name="case_outbox",
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.drop_table("case_outbox")
    op.drop_index("ix_case_history_case_version", table_name="case_state_history")
    op.drop_table("case_state_history")
    op.drop_index("ix_encounters_case_occurred", table_name="encounters")
    op.drop_table("encounters")
    op.drop_index("ix_cases_facility_state", table_name="cases")
    op.drop_index("ix_cases_synthetic_subject", table_name="cases")
    op.drop_table("cases")
