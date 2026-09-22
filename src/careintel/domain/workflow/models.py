"""
Async task domain models.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from typing import Any

from careintel.domain.workflow.task_states import AsyncTaskStatus


@dataclass(frozen=True)
class AsyncTaskPayload:
    """
    Strongly typed payload for background execution.
    """

    task_type: str
    task_version: int
    entity_type: str
    entity_id: uuid.UUID
    case_id: uuid.UUID
    actor_id: uuid.UUID
    correlation_id: str
    config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for ORM persistence."""
        return {
            "task_type": self.task_type,
            "task_version": self.task_version,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "case_id": str(self.case_id),
            "actor_id": str(self.actor_id),
            "correlation_id": self.correlation_id,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AsyncTaskPayload:
        """Deserialize from ORM payload."""
        return cls(
            task_type=data["task_type"],
            task_version=data["task_version"],
            entity_type=data["entity_type"],
            entity_id=uuid.UUID(data["entity_id"]),
            case_id=uuid.UUID(data["case_id"]),
            actor_id=uuid.UUID(data["actor_id"]),
            correlation_id=data["correlation_id"],
            config=data.get("config", {}),
        )


@dataclass
class AsyncTask:
    """
    Domain model for a durable background task execution.
    """

    id: uuid.UUID
    task_type: str
    task_version: int
    idempotency_key: str
    case_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    actor_id: uuid.UUID
    correlation_id: str
    causation_id: str | None
    status: AsyncTaskStatus
    attempt_count: int
    max_attempts: int
    celery_task_id: str | None
    payload: AsyncTaskPayload
    result: dict[str, Any] | None
    error_category: str | None
    failure_reason: str | None
    created_at: datetime.datetime
    queued_at: datetime.datetime | None
    started_at: datetime.datetime | None
    heartbeat_at: datetime.datetime | None
    completed_at: datetime.datetime | None
