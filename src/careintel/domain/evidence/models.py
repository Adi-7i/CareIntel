"""
Evidence domain models.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Any

from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.evidence.states import EvidenceState


@dataclass(frozen=True)
class EvidenceAggregate:
    """
    Root aggregate for an Evidence record.
    """

    evidence_id: uuid.UUID
    case_id: uuid.UUID
    modality: EvidenceModality
    state: EvidenceState
    content_type: str
    size_bytes: int
    created_by: uuid.UUID
    created_at: datetime.datetime

    encounter_id: uuid.UUID | None = None
    original_filename: str | None = None
    sha256_checksum: str | None = None
    source_language: str | None = None
    storage_key: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
