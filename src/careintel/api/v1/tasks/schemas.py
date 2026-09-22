"""
Task API schemas.
"""

import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class AsyncTaskResponse(BaseModel):
    """Response model for an async task."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_type: str
    status: str
    case_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    correlation_id: str

    error_category: str | None = None
    failure_reason: str | None = None

    created_at: datetime.datetime
    queued_at: datetime.datetime | None = None
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
