"""
Retrieval ORM models.

Tables:
- retrieval_runs       — Audit record for each retrieval operation.
- retrieval_candidates — Individual candidates returned from retrieval.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from careintel.persistence.base import Base


class RetrievalRunORM(Base):
    """
    Audit record for a single retrieval operation.

    Idempotency: UNIQUE(case_id, query_hash, corpus_version, search_mode)
    so duplicate retrieval requests return the existing run.
    """

    __tablename__ = "retrieval_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # NULL for knowledge-only queries (no patient scope)
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=True,
    )
    # SHA-256 of the normalized query text
    query_hash: Mapped[str] = mapped_column(String, nullable=False)
    # DENSE, SPARSE, or HYBRID
    search_mode: Mapped[str] = mapped_column(String, nullable=False)
    # Corpus version used; NULL if not pinned
    corpus_version: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("embedding_versions.id", ondelete="RESTRICT"),
        nullable=True,
    )
    applied_filters: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    zero_result_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    __table_args__ = (
        # Idempotency: same query+corpus+mode returns existing run
        UniqueConstraint(
            "case_id",
            "query_hash",
            "corpus_version",
            "search_mode",
            name="uq_retrieval_run_idempotency",
        ),
        Index("ix_retrieval_runs_case", "case_id"),
        Index("ix_retrieval_runs_query_hash", "query_hash"),
    )


class RetrievalCandidateORM(Base):
    """
    An individual candidate result from a retrieval run.

    Preserves dense, sparse, and fusion scores separately for audit.
    """

    __tablename__ = "retrieval_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    retrieval_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("retrieval_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    # KNOWLEDGE_CHUNK or PATIENT_EVIDENCE
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    # knowledge_chunks.id or evidence.id
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    dense_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sparse_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fusion_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation_locator: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    __table_args__ = (Index("ix_retrieval_candidates_run", "retrieval_run_id"),)
