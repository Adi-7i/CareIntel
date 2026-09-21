"""
Knowledge domain status enums.

These govern the lifecycle of knowledge sources and their published versions.
"""

from __future__ import annotations

from enum import StrEnum


class PublicationStatus(StrEnum):
    """
    Lifecycle status of a knowledge source.

    DRAFT      — Source is being prepared; not yet available for retrieval.
    PUBLISHED  — Source is active and available for retrieval.
    RETIRED    — Source is no longer active; historical records preserved.
    """

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    RETIRED = "RETIRED"


class ChunkStatus(StrEnum):
    """
    Status of an individual knowledge chunk.

    ACTIVE     — Chunk is available for retrieval.
    SUPERSEDED — Chunk exists in a newer version; preserved for provenance.
    """

    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
