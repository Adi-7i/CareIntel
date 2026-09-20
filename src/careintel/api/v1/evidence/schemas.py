"""
Evidence schemas.
"""

import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.evidence.states import EvidenceState


class RegisterTextRequest(BaseModel):
    """Payload to register text evidence."""

    case_id: uuid.UUID
    text_content: str = Field(..., max_length=20000)
    consent_id: uuid.UUID
    encounter_id: uuid.UUID | None = None
    source_language: str | None = None


class EvidenceResponse(BaseModel):
    """Response model for evidence."""

    evidence_id: uuid.UUID
    case_id: uuid.UUID
    encounter_id: uuid.UUID | None
    modality: EvidenceModality
    state: EvidenceState
    content_type: str
    size_bytes: int
    original_filename: str | None
    source_language: str | None
    created_by: uuid.UUID
    created_at: datetime.datetime
    provenance: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponse(BaseModel):
    """List response for a case's evidence."""

    case_id: uuid.UUID
    evidence: list[EvidenceResponse]


class SecureDownloadResponse(BaseModel):
    """SAS URL response."""

    download_url: str
    expires_at: datetime.datetime
