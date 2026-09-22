"""
processing

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-20 13:15:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. processing_runs
    op.create_table(
        "processing_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("processor_type", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("config_version", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processing_runs")),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            name=op.f("fk_processing_runs_evidence_id_evidence"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "evidence_id",
            "processor_type",
            "config_version",
            name=op.f("uq_processing_run_idempotency"),
        ),
    )
    op.create_index(
        "ix_processing_run_evidence",
        "processing_runs",
        ["evidence_id"],
        unique=False,
    )

    # 2. ocr_pages
    op.create_table(
        "ocr_pages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ocr_pages")),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["processing_runs.id"],
            name=op.f("fk_ocr_pages_run_id_processing_runs"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("run_id", "page_number", name=op.f("uq_ocr_page_number")),
    )
    op.create_index(
        "ix_ocr_page_run",
        "ocr_pages",
        ["run_id"],
        unique=False,
    )

    # 3. ocr_regions
    op.create_table(
        "ocr_regions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("reading_order", sa.Integer(), nullable=False),
        sa.Column("bounding_box", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ocr_regions")),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["ocr_pages.id"],
            name=op.f("fk_ocr_regions_page_id_ocr_pages"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_ocr_region_page",
        "ocr_regions",
        ["page_id"],
        unique=False,
    )

    # 4. ocr_table_candidates
    op.create_table(
        "ocr_table_candidates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cells_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ocr_table_candidates")),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["ocr_pages.id"],
            name=op.f("fk_ocr_table_candidates_page_id_ocr_pages"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_ocr_table_page",
        "ocr_table_candidates",
        ["page_id"],
        unique=False,
    )

    # 5. transcript_runs
    op.create_table(
        "transcript_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("processing_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_version", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transcript_runs")),
        sa.ForeignKeyConstraint(
            ["processing_run_id"],
            ["processing_runs.id"],
            name=op.f("fk_transcript_runs_processing_run_id_processing_runs"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("processing_run_id", name=op.f("uq_transcript_runs_processing_run_id")),
    )

    # 6. transcript_segments
    op.create_table(
        "transcript_segments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("transcript_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_time_ms", sa.Integer(), nullable=False),
        sa.Column("end_time_ms", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("speaker_label", sa.String(), nullable=True),
        sa.Column("is_silence", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transcript_segments")),
        sa.ForeignKeyConstraint(
            ["transcript_run_id"],
            ["transcript_runs.id"],
            name=op.f("fk_transcript_segments_transcript_run_id_transcript_runs"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_transcript_segment_run",
        "transcript_segments",
        ["transcript_run_id"],
        unique=False,
    )

    # 7. language_results
    op.create_table(
        "language_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("processing_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("detected_language", sa.String(), nullable=True),
        sa.Column("detected_confidence", sa.Float(), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("translation_text", sa.Text(), nullable=True),
        sa.Column("translation_provider", sa.String(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_language_results")),
        sa.ForeignKeyConstraint(
            ["processing_run_id"],
            ["processing_runs.id"],
            name=op.f("fk_language_results_processing_run_id_processing_runs"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "processing_run_id", name=op.f("uq_language_results_processing_run_id")
        ),
    )

    # 8. extraction_runs
    op.create_table(
        "extraction_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("processing_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_version", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extraction_runs")),
        sa.ForeignKeyConstraint(
            ["processing_run_id"],
            ["processing_runs.id"],
            name=op.f("fk_extraction_runs_processing_run_id_processing_runs"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("processing_run_id", name=op.f("uq_extraction_runs_processing_run_id")),
    )

    # 9. extracted_candidates
    op.create_table(
        "extracted_candidates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("extraction_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_type", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "provenance_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extracted_candidates")),
        sa.ForeignKeyConstraint(
            ["extraction_run_id"],
            ["extraction_runs.id"],
            name=op.f("fk_extracted_candidates_extraction_run_id_extraction_runs"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_extracted_candidate_run",
        "extracted_candidates",
        ["extraction_run_id"],
        unique=False,
    )

    # Seed processing_read and processing_write to permissions and assign to roles
    op.execute(
        """
        INSERT INTO permissions (code)
        VALUES ('processing:read'), ('processing:write')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE r.name IN ('doctor', 'medical_officer', 'reviewer', 'admin')
          AND p.code IN ('processing:read', 'processing:write')
        ON CONFLICT DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_extracted_candidate_run", table_name="extracted_candidates")
    op.drop_table("extracted_candidates")
    op.drop_table("extraction_runs")
    op.drop_table("language_results")
    op.drop_index("ix_transcript_segment_run", table_name="transcript_segments")
    op.drop_table("transcript_segments")
    op.drop_table("transcript_runs")
    op.drop_index("ix_ocr_table_page", table_name="ocr_table_candidates")
    op.drop_table("ocr_table_candidates")
    op.drop_index("ix_ocr_region_page", table_name="ocr_regions")
    op.drop_table("ocr_regions")
    op.drop_index("ix_ocr_page_run", table_name="ocr_pages")
    op.drop_table("ocr_pages")
    op.drop_index("ix_processing_run_evidence", table_name="processing_runs")
    op.drop_table("processing_runs")
