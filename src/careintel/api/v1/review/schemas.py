from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from careintel.domain.review.states import ReviewDecisionType


class QueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    encounter_id: uuid.UUID | None
    status: str
    assigned_reviewer_id: uuid.UUID | None
    priority_bucket: str
    version: int


class EnterQueueRequest(BaseModel):
    encounter_id: uuid.UUID | None = None


class AssignReviewerRequest(BaseModel):
    reviewer_id: uuid.UUID
    expected_version: int = Field(ge=1)


class ReassignReviewerRequest(BaseModel):
    reviewer_id: uuid.UUID
    reason: str = Field(min_length=1, max_length=1000)
    expected_version: int = Field(ge=1)


class VersionRequest(BaseModel):
    expected_version: int = Field(ge=1)


class DraftActionRequest(BaseModel):
    expected_draft_version: int = Field(ge=1)
    expected_queue_version: int = Field(ge=1)


class RejectDraftRequest(DraftActionRequest):
    rationale: str = Field(min_length=1, max_length=4000)


class EditDraftRequest(DraftActionRequest):
    edited_content: dict[str, Any]
    rationale: str | None = Field(default=None, max_length=4000)


class DraftActionResponse(BaseModel):
    id: uuid.UUID
    reviewer_status: str
    reviewer_id: uuid.UUID | None
    version: int


class ReviewDecisionRequest(BaseModel):
    draft_id: uuid.UUID
    decision_type: ReviewDecisionType
    rationale: str | None = Field(default=None, max_length=4000)
    expected_case_version: int = Field(ge=1)
    expected_queue_version: int = Field(ge=1)
    expected_draft_version: int = Field(ge=1)


class ReviewDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    reviewer_id: uuid.UUID
    draft_id: uuid.UUID | None
    draft_version: int | None
    decision_type: str
    case_version: int
