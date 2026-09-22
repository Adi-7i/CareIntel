"""
Retrieval domain models.

Defines value objects for the hybrid retrieval layer.

Design invariants:
- Retrieval results carry full provenance for audit.
- Dense, sparse, and fusion scores are preserved separately.
- Zero-result state is explicit, never silently collapsed.
- Patient evidence retrieval is always case-scoped.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field

from careintel.domain.retrieval.status import RetrievalStatus, SearchMode, SourceType


@dataclass(frozen=True)
class RetrievalQuery:
    """
    Encapsulates a retrieval query with all relevant parameters.

    The query_text is normalized before hashing for idempotency.
    """

    query_text: str
    search_mode: SearchMode
    # Optional case scope — required for patient evidence retrieval
    case_id: uuid.UUID | None
    # Optional corpus/embedding version pinning
    corpus_version: str | None
    embedding_version_key: str | None
    # Metadata filters (e.g. source_type, publication_status)
    filters: dict[str, str] = field(default_factory=dict)
    # Maximum number of final candidates to return
    top_k: int = 10


@dataclass(frozen=True)
class RetrievalCandidate:
    """
    A single candidate returned from retrieval.

    Carries both the source reference and all scoring information
    to support provenance and auditability.
    """

    candidate_id: uuid.UUID
    retrieval_run_id: uuid.UUID
    source_type: SourceType
    # References knowledge_chunks.id or evidence.id depending on source_type
    source_id: uuid.UUID
    rank: int  # 1-based rank in final sorted results
    dense_score: float | None  # Cosine similarity (0-1), None if sparse-only
    sparse_score: float | None  # ts_rank_cd score, None if dense-only
    fusion_score: float | None  # RRF score, None if single-mode
    # Human-readable citation: e.g. "Source: WHO Guideline v1.2, para 4"
    citation_locator: str | None


@dataclass(frozen=True)
class RetrievalMetadata:
    """
    Audit metadata for a completed retrieval run.

    Preserved alongside AI context so historical queries remain explainable.
    """

    retrieval_run_id: uuid.UUID
    query_hash: str  # SHA-256 of normalized query text
    search_mode: SearchMode
    corpus_version: str | None
    embedding_version_key: str | None
    applied_filters: dict[str, str]
    candidate_count: int
    status: RetrievalStatus
    zero_result_reason: str | None
    created_at: datetime.datetime


@dataclass(frozen=True)
class RetrievalResult:
    """
    Complete output of a retrieval operation.

    Carries candidates with full scoring and metadata for audit.
    """

    metadata: RetrievalMetadata
    candidates: list[RetrievalCandidate] = field(default_factory=list)
