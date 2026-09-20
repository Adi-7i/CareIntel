"""
Evidence use case commands.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from careintel.domain.evidence.modality import EvidenceModality


@dataclass(frozen=True)
class RegisterTextEvidenceCommand:
    """Command to register raw text evidence."""

    case_id: uuid.UUID
    text_content: str
    actor_id: uuid.UUID
    correlation_id: str
    consent_id: uuid.UUID
    encounter_id: uuid.UUID | None = None
    source_language: str | None = None


@dataclass(frozen=True)
class UploadFileEvidenceCommand:
    """Command to initiate a file upload."""

    case_id: uuid.UUID
    modality: EvidenceModality
    declared_filename: str
    declared_content_type: str
    actor_id: uuid.UUID
    correlation_id: str
    consent_id: uuid.UUID
    encounter_id: uuid.UUID | None = None
