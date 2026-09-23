"""Link extraction runs to their exact source processing artifact.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "extraction_runs",
        sa.Column("source_processing_run_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_extraction_runs_source_processing_run_id_processing_runs",
        "extraction_runs",
        "processing_runs",
        ["source_processing_run_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_extraction_runs_source_processing_run",
        "extraction_runs",
        ["source_processing_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_extraction_runs_source_processing_run", table_name="extraction_runs")
    op.drop_constraint(
        "fk_extraction_runs_source_processing_run_id_processing_runs",
        "extraction_runs",
        type_="foreignkey",
    )
    op.drop_column("extraction_runs", "source_processing_run_id")
