"""0007 retrieval ai

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-21

Phase 7: Retrieval + AI + Safety

Tables introduced:
- knowledge_sources     — Trusted knowledge documents/sources
- knowledge_versions    — Immutable versioned snapshots
- knowledge_chunks      — Text passages for retrieval (with tsvector FTS)
- embedding_versions    — Embedding model registry
- chunk_embeddings      — pgvector embeddings (VECTOR type via raw DDL)
- retrieval_runs        — Retrieval audit records
- retrieval_candidates  — Individual retrieval results
- ai_runs               — AI task execution records
- ai_drafts             — Validated AI output awaiting reviewer decision
- policy_decisions      — Deterministic policy check results

DEPENDENCY: Requires pgvector extension in PostgreSQL.
If pgvector is unavailable, this migration will fail explicitly.
Do NOT install pgvector at OS level — it must be enabled in the
external PostgreSQL instance.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── pgvector extension ────────────────────────────────────────────────────
    # If the external PostgreSQL does not have pgvector, this will raise.
    # That is intentional: we do not silently fall back to a non-vector search.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── knowledge_sources ─────────────────────────────────────────────────────
    op.create_table(
        "knowledge_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("owner", sa.String(), nullable=True),
        sa.Column("publication_status", sa.String(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("retirement_date", sa.Date(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "metadata_json",
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
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_knowledge_sources_created_by_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_sources"),
    )
    op.create_index("ix_knowledge_sources_status", "knowledge_sources", ["publication_status"])
    op.create_index("ix_knowledge_sources_type", "knowledge_sources", ["source_type"])

    # ── knowledge_versions ────────────────────────────────────────────────────
    op.create_table(
        "knowledge_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_key", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("corpus_version", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["knowledge_sources.id"],
            name="fk_knowledge_versions_source_id_knowledge_sources",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_versions"),
        sa.UniqueConstraint("source_id", "version_key", name="uq_knowledge_version_key"),
    )
    op.create_index("ix_knowledge_versions_source", "knowledge_versions", ["source_id"])
    op.create_index("ix_knowledge_versions_corpus", "knowledge_versions", ["corpus_version"])

    # ── knowledge_chunks ──────────────────────────────────────────────────────
    op.create_table(
        "knowledge_chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["knowledge_versions.id"],
            name="fk_knowledge_chunks_version_id_knowledge_versions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_chunks"),
        sa.UniqueConstraint("version_id", "chunk_index", name="uq_chunk_index"),
    )
    op.create_index("ix_knowledge_chunks_version", "knowledge_chunks", ["version_id"])
    op.create_index("ix_knowledge_chunks_status", "knowledge_chunks", ["status"])

    # Add tsvector column for full-text search via raw DDL
    op.execute(
        "ALTER TABLE knowledge_chunks "
        "ADD COLUMN fts_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED"
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_fts ON knowledge_chunks USING GIN (fts_vector)"
    )

    # ── embedding_versions ────────────────────────────────────────────────────
    op.create_table(
        "embedding_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("version_key", sa.String(), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_embedding_versions"),
        sa.UniqueConstraint("version_key", name="uq_embedding_versions_version_key"),
    )
    op.create_index("ix_embedding_versions_key", "embedding_versions", ["version_key"])

    # ── chunk_embeddings ──────────────────────────────────────────────────────
    op.create_table(
        "chunk_embeddings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["knowledge_chunks.id"],
            name="fk_chunk_embeddings_chunk_id_knowledge_chunks",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["embedding_version_id"],
            ["embedding_versions.id"],
            name="fk_chunk_embeddings_embedding_version_id_embedding_versions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chunk_embeddings"),
        sa.UniqueConstraint(
            "chunk_id", "embedding_version_id", name="uq_chunk_embedding_version"
        ),
    )
    op.create_index("ix_chunk_embeddings_chunk", "chunk_embeddings", ["chunk_id"])
    op.create_index("ix_chunk_embeddings_version", "chunk_embeddings", ["embedding_version_id"])

    # Add pgvector embedding column via raw DDL.
    # Dimension 768 is the demo/default dimension; production adapters
    # may use different dimensions tracked via embedding_versions.
    # NOTE: A single fixed vector dimension per table is a pgvector constraint.
    # Multiple embedding dimensions are handled by separate tables or future migration.
    op.execute(
        "ALTER TABLE chunk_embeddings ADD COLUMN embedding vector(768)"
    )
    op.execute(
        "CREATE INDEX ix_chunk_embeddings_hnsw ON chunk_embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # ── retrieval_runs ────────────────────────────────────────────────────────
    op.create_table(
        "retrieval_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query_hash", sa.String(), nullable=False),
        sa.Column("search_mode", sa.String(), nullable=False),
        sa.Column("corpus_version", sa.String(), nullable=True),
        sa.Column("embedding_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "applied_filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("zero_result_reason", sa.String(), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name="fk_retrieval_runs_case_id_cases",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["embedding_version_id"],
            ["embedding_versions.id"],
            name="fk_retrieval_runs_embedding_version_id_embedding_versions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_retrieval_runs"),
        sa.UniqueConstraint(
            "case_id", "query_hash", "corpus_version", "search_mode",
            name="uq_retrieval_run_idempotency",
        ),
    )
    op.create_index("ix_retrieval_runs_case", "retrieval_runs", ["case_id"])
    op.create_index("ix_retrieval_runs_query_hash", "retrieval_runs", ["query_hash"])

    # ── retrieval_candidates ──────────────────────────────────────────────────
    op.create_table(
        "retrieval_candidates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("retrieval_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("dense_score", sa.Float(), nullable=True),
        sa.Column("sparse_score", sa.Float(), nullable=True),
        sa.Column("fusion_score", sa.Float(), nullable=True),
        sa.Column("citation_locator", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_run_id"],
            ["retrieval_runs.id"],
            name="fk_retrieval_candidates_retrieval_run_id_retrieval_runs",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_retrieval_candidates"),
    )
    op.create_index(
        "ix_retrieval_candidates_run", "retrieval_candidates", ["retrieval_run_id"]
    )

    # ── ai_runs ───────────────────────────────────────────────────────────────
    op.create_table(
        "ai_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=False),
        sa.Column("retrieval_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("input_hash", sa.String(), nullable=True),
        sa.Column("output_hash", sa.String(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "usage_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_category", sa.String(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_ai_runs_actor_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name="fk_ai_runs_case_id_cases",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_run_id"],
            ["retrieval_runs.id"],
            name="fk_ai_runs_retrieval_run_id_retrieval_runs",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ai_runs"),
        sa.UniqueConstraint(
            "case_id", "task_type", "input_hash", "prompt_version",
            name="uq_ai_run_idempotency",
        ),
    )
    op.create_index("ix_ai_runs_case", "ai_runs", ["case_id"])
    op.create_index("ix_ai_runs_status", "ai_runs", ["status"])
    op.create_index("ix_ai_runs_actor", "ai_runs", ["actor_id"])

    # ── ai_drafts ─────────────────────────────────────────────────────────────
    op.create_table(
        "ai_drafts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("ai_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "content_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("validation_status", sa.String(), nullable=False),
        sa.Column(
            "validation_errors",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "provenance_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("reviewer_status", sa.String(), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ai_run_id"],
            ["ai_runs.id"],
            name="fk_ai_drafts_ai_run_id_ai_runs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            name="fk_ai_drafts_reviewer_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ai_drafts"),
        sa.UniqueConstraint("ai_run_id", name="uq_ai_drafts_ai_run_id"),
    )
    op.create_index("ix_ai_drafts_reviewer_status", "ai_drafts", ["reviewer_status"])

    # ── policy_decisions ──────────────────────────────────────────────────────
    op.create_table(
        "policy_decisions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("ai_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("check_type", sa.String(), nullable=False),
        sa.Column("policy_version", sa.String(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column(
            "detail_json",
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
        sa.ForeignKeyConstraint(
            ["ai_run_id"],
            ["ai_runs.id"],
            name="fk_policy_decisions_ai_run_id_ai_runs",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_policy_decisions"),
    )
    op.create_index("ix_policy_decisions_ai_run", "policy_decisions", ["ai_run_id"])


def downgrade() -> None:
    op.drop_table("policy_decisions")
    op.drop_table("ai_drafts")
    op.drop_table("ai_runs")
    op.drop_table("retrieval_candidates")
    op.drop_table("retrieval_runs")
    op.drop_table("chunk_embeddings")
    op.drop_table("embedding_versions")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_versions")
    op.drop_table("knowledge_sources")
    # Do not drop vector extension — other tables may depend on it
