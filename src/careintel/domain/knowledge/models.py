"""
Knowledge domain models.

Defines the immutable value objects for the trusted knowledge layer.

Trusted knowledge may contain approved:
- healthcare guidance
- institutional procedures
- approved public-health material
- facility-specific information
- approved operational documents

CRITICAL:
- Patient data must NEVER automatically become trusted knowledge.
- AI-generated content must NEVER automatically become trusted knowledge.
- The exact corpus authority and sources must remain configurable.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field

from careintel.domain.knowledge.status import ChunkStatus, PublicationStatus


@dataclass(frozen=True)
class KnowledgeSource:
    """
    A versioned, authoritative knowledge source.

    Represents a single document, guideline, procedure, or policy
    from an approved institutional or public-health corpus.
    """

    source_id: uuid.UUID
    name: str
    source_type: str  # e.g. 'guideline', 'procedure', 'policy', 'operational'
    owner: str | None  # Institutional owner; None = system-managed
    publication_status: PublicationStatus
    effective_date: datetime.date | None
    retirement_date: datetime.date | None
    created_by: uuid.UUID
    created_at: datetime.datetime
    # Arbitrary configurable metadata (e.g. setting, population, language)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeVersion:
    """
    An immutable snapshot of a KnowledgeSource at a specific version.

    Versions are created when source content changes.
    Historical versions are preserved for provenance.
    """

    version_id: uuid.UUID
    source_id: uuid.UUID
    version_key: str  # e.g. 'v1.0', 'v2.1'
    content_hash: str  # SHA-256 of full source content for integrity
    corpus_version: str  # Corpus-wide version tag (e.g. '2024-Q4')
    created_at: datetime.datetime


@dataclass(frozen=True)
class KnowledgeChunk:
    """
    A discrete text passage derived from a KnowledgeVersion.

    Chunks are the unit of retrieval. Each chunk carries provenance
    back to its parent version and source.

    Chunks are immutable once created. If source content changes,
    a new KnowledgeVersion and new chunks are created.
    """

    chunk_id: uuid.UUID
    version_id: uuid.UUID
    chunk_index: int  # Ordering within the version (0-based)
    content: str
    token_count: int | None
    status: ChunkStatus = ChunkStatus.ACTIVE
    # Optional per-chunk metadata (e.g. section title, page number)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingVersion:
    """
    Registry entry for a specific embedding model configuration.

    Tracks provider, model, and dimension so incompatible embeddings
    are never mixed during retrieval.
    """

    embedding_version_id: uuid.UUID
    provider: str  # e.g. 'openai', 'demo'
    model: str  # e.g. 'text-embedding-3-small', 'demo-fixed-768'
    dimension: int
    version_key: str  # Unique human-readable key, e.g. 'openai-te3-small-1536'
    created_at: datetime.datetime


@dataclass(frozen=True)
class ChunkEmbedding:
    """
    A computed vector embedding for a specific chunk + embedding version.

    The embedding vector itself is stored in pgvector.
    This domain object carries the provenance metadata.
    """

    embedding_id: uuid.UUID
    chunk_id: uuid.UUID
    embedding_version_id: uuid.UUID
    created_at: datetime.datetime
    # The actual vector is stored in persistence, not in the domain object.
    # dimension and provider are accessible via EmbeddingVersion.
