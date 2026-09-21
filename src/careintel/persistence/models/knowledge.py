"""
Knowledge ORM models for the trusted knowledge corpus.

Tables:
- knowledge_sources     — Authoritative knowledge documents/sources.
- knowledge_versions    — Immutable versioned snapshots of a source.
- knowledge_chunks      — Discrete text passages ready for retrieval.
- embedding_versions    — Registry of embedding model configurations.
- chunk_embeddings      — pgvector embeddings for knowledge chunks.
"""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from careintel.persistence.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class KnowledgeSourceORM(Base, TimestampMixin):
    """Authoritative knowledge source (document, guideline, procedure, etc.)."""

    __tablename__ = "knowledge_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    # Institutional owner; None = system-managed
    owner: Mapped[str | None] = mapped_column(String, nullable=True)
    publication_status: Mapped[str] = mapped_column(
        String, nullable=False, default="DRAFT"
    )
    effective_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    retirement_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    # Configurable metadata: setting, population, language, facility, etc.
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_knowledge_sources_status", "publication_status"),
        Index("ix_knowledge_sources_type", "source_type"),
    )


class KnowledgeVersionORM(Base):
    """
    Immutable versioned snapshot of a KnowledgeSource.

    Created when source content changes. Historical versions are
    preserved for provenance — never deleted.
    """

    __tablename__ = "knowledge_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_key: Mapped[str] = mapped_column(String, nullable=False)
    # SHA-256 of full source content for integrity verification
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    # Corpus-wide version tag (e.g. '2024-Q4')
    corpus_version: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("source_id", "version_key", name="uq_knowledge_version_key"),
        Index("ix_knowledge_versions_source", "source_id"),
        Index("ix_knowledge_versions_corpus", "corpus_version"),
    )


class KnowledgeChunkORM(Base):
    """
    A discrete text passage derived from a KnowledgeVersion.

    Chunks are the retrieval unit. Immutable once created.
    FTS vector is maintained by a trigger or application-level update.
    """

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    # PostgreSQL tsvector for full-text search
    # Populated via application-level update using to_tsvector('english', content)
    # Column type is TEXT here; cast in queries. Using TSVECTOR type via raw DDL
    # in migration for proper GIN indexing.
    # NOTE: We use a separate migration DDL statement for this column rather than
    # SQLAlchemy column type to avoid introducing tsvector as a Python type.

    __table_args__ = (
        UniqueConstraint("version_id", "chunk_index", name="uq_chunk_index"),
        Index("ix_knowledge_chunks_version", "version_id"),
        Index("ix_knowledge_chunks_status", "status"),
    )


class EmbeddingVersionORM(Base):
    """
    Registry of embedding model configurations.

    Tracks provider, model, and dimension to prevent mixing
    incompatible embeddings during retrieval.
    """

    __tablename__ = "embedding_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    version_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    __table_args__ = (Index("ix_embedding_versions_key", "version_key"),)


class ChunkEmbeddingORM(Base):
    """
    pgvector embedding for a specific chunk + embedding version.

    The `embedding` column uses pgvector VECTOR type defined via raw DDL
    in the migration. SQLAlchemy column is typed as Text as placeholder;
    actual queries use raw SQL or pgvector's SQLAlchemy integration.
    """

    __tablename__ = "chunk_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    embedding_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("embedding_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    # NOTE: The actual `embedding vector(N)` column is added via raw DDL in
    # the Alembic migration because SQLAlchemy does not natively model
    # parameterized VECTOR types without pgvector's SQLAlchemy extension types.
    # Queries against this column use pgvector's SQLAlchemy types from the
    # pgvector package (pgvector.sqlalchemy.Vector).

    __table_args__ = (
        UniqueConstraint(
            "chunk_id", "embedding_version_id", name="uq_chunk_embedding_version"
        ),
        Index("ix_chunk_embeddings_chunk", "chunk_id"),
        Index("ix_chunk_embeddings_version", "embedding_version_id"),
    )
