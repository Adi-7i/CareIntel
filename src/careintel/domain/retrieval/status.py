"""
Retrieval domain — status and search mode enums.
"""

from __future__ import annotations

from enum import StrEnum


class RetrievalStatus(StrEnum):
    """
    Status of a retrieval run.

    COMPLETED    — Retrieval completed with at least one candidate.
    ZERO_RESULTS — Retrieval completed successfully but no candidates matched.
    FAILED       — Retrieval failed due to a provider or system error.
    """

    COMPLETED = "COMPLETED"
    ZERO_RESULTS = "ZERO_RESULTS"
    FAILED = "FAILED"


class SearchMode(StrEnum):
    """
    Search strategy used for retrieval.

    DENSE  — Vector similarity search (pgvector cosine distance).
    SPARSE — Full-text search (PostgreSQL tsvector/tsquery).
    HYBRID — Dense + sparse with deterministic RRF fusion.
    """

    DENSE = "DENSE"
    SPARSE = "SPARSE"
    HYBRID = "HYBRID"


class SourceType(StrEnum):
    """
    Origin type of a retrieval candidate.

    KNOWLEDGE_CHUNK    — From the trusted institutional knowledge corpus.
    PATIENT_EVIDENCE   — From patient-specific case evidence.
    """

    KNOWLEDGE_CHUNK = "KNOWLEDGE_CHUNK"
    PATIENT_EVIDENCE = "PATIENT_EVIDENCE"
