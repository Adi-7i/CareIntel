"""Advisory AI request and response contracts."""

import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from careintel.domain.ai.status import DraftReviewerStatus, TaskType, ValidationStatus


class ExecuteAdvisoryRequest(BaseModel):
    retrieval_run_id: uuid.UUID
    task_type: TaskType


class ValidationErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step: str
    code: str
    detail: str


class ClaimProvenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_text: str
    status: str
    supporting_source_ids: list[uuid.UUID]


class AIDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    draft_id: uuid.UUID
    ai_run_id: uuid.UUID
    content: dict[str, object]
    validation_status: ValidationStatus
    validation_errors: list[ValidationErrorResponse]
    claim_provenance: list[ClaimProvenanceResponse]
    reviewer_status: DraftReviewerStatus
    reviewer_id: uuid.UUID | None
    reviewed_at: datetime.datetime | None
    created_at: datetime.datetime
