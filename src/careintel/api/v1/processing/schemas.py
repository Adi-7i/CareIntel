"""
Processing API Schemas.
"""

import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.processing.processor_type import ProcessorType


class TriggerProcessingRequest(BaseModel):
    """Request schema to trigger a processing run."""

    evidence_id: uuid.UUID
    processor_type: str = Field(..., description="e.g., document_ocr, speech_transcription")
    parameters: dict[str, Any] = Field(default_factory=dict)


class TriggerProcessingResponse(BaseModel):
    """Response schema when processing is triggered."""

    run_id: uuid.UUID
    message: str = "Processing triggered successfully."

    model_config = ConfigDict(from_attributes=True)


class ProcessingRunResponse(BaseModel):
    """Persisted processing state and provider metadata."""

    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    evidence_id: uuid.UUID
    processor_type: ProcessorType
    provider: str
    status: ProcessingStatus
    config_version: str
    started_at: datetime.datetime | None
    completed_at: datetime.datetime | None
    failure_reason: str | None
