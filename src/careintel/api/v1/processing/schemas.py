"""
Processing API Schemas.
"""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
