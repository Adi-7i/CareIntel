from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class CreateEscalationRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=4000)
    expected_case_version: int = Field(ge=1)
    expected_queue_version: int = Field(ge=1)


class ResolveEscalationRequest(BaseModel):
    resolution_notes: str = Field(min_length=1, max_length=4000)
    expected_case_version: int = Field(ge=1)
    expected_queue_version: int = Field(ge=1)


class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    escalated_by: uuid.UUID
    status: str
    reason: str
    resolved_by: uuid.UUID | None
    resolution_notes: str | None
