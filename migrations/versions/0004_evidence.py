"""
evidence

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-20 11:15:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. evidence table
    op.create_table(
        "evidence",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("encounter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("modality", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=True),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_checksum", sa.String(), nullable=True),
        sa.Column("source_language", sa.String(), nullable=True),
        sa.Column("storage_key", sa.String(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence")),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_evidence_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounters.id"],
            name=op.f("fk_evidence_encounter_id_encounters"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_evidence_created_by_users"),
        ),
        sa.UniqueConstraint("case_id", "sha256_checksum", name=op.f("uq_evidence_case_sha256")),
    )
    op.create_index(
        "ix_evidence_case",
        "evidence",
        ["case_id"],
        unique=False,
    )

    # 2. evidence_text_content table
    op.create_table(
        "evidence_text_content",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_text_content")),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            name=op.f("fk_evidence_text_content_evidence_id_evidence"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("evidence_id", name=op.f("uq_evidence_text_content_evidence_id")),
    )

    # 3. evidence_state_history table
    op.create_table(
        "evidence_state_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_state", sa.String(), nullable=False),
        sa.Column("to_state", sa.String(), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "transitioned_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_state_history")),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            name=op.f("fk_evidence_state_history_evidence_id_evidence"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_evidence_state_history_actor_id_users"),
        ),
    )
    op.create_index(
        "ix_evidence_history_evidence",
        "evidence_state_history",
        ["evidence_id"],
        unique=False,
    )

    # 4. evidence_outbox table
    op.create_table(
        "evidence_outbox",
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
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_outbox")),
    )
    op.create_index(
        "ix_evidence_outbox_unpublished",
        "evidence_outbox",
        ["id"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )

    # Seed evidence_read and evidence_write to permissions and assign to roles
    op.execute(
        """
        INSERT INTO permissions (code)
        VALUES ('evidence:read'), ('evidence:write')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE r.name IN ('doctor', 'medical_officer', 'reviewer', 'admin')
          AND p.code IN ('evidence:read', 'evidence:write')
        ON CONFLICT DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evidence_outbox_unpublished",
        table_name="evidence_outbox",
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.drop_table("evidence_outbox")
    op.drop_index("ix_evidence_history_evidence", table_name="evidence_state_history")
    op.drop_table("evidence_state_history")
    op.drop_table("evidence_text_content")
    op.drop_index("ix_evidence_case", table_name="evidence")
    op.drop_table("evidence")
