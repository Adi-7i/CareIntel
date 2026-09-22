"""
Async Task Service.
"""

from __future__ import annotations

import datetime
import uuid

from careintel.core.errors import InvalidTransitionError
from careintel.domain.workflow.models import AsyncTask, AsyncTaskPayload
from careintel.domain.workflow.task_state_machine import TaskStateMachine
from careintel.domain.workflow.task_states import AsyncTaskStatus
from careintel.persistence.models.workflow import AsyncTaskORM
from careintel.persistence.repositories.task_repo import AsyncTaskRepository


class AsyncTaskService:
    """Service for managing the durable async task lifecycle."""

    def __init__(self, task_repo: AsyncTaskRepository) -> None:
        self.task_repo = task_repo

    def _to_domain(self, orm: AsyncTaskORM) -> AsyncTask:
        return AsyncTask(
            id=orm.id,
            task_type=orm.task_type,
            task_version=orm.task_version,
            idempotency_key=orm.idempotency_key,
            case_id=orm.case_id,
            entity_type=orm.entity_type,
            entity_id=orm.entity_id,
            actor_id=orm.actor_id,
            correlation_id=orm.correlation_id,
            causation_id=orm.causation_id,
            status=AsyncTaskStatus(orm.status),
            attempt_count=orm.attempt_count,
            max_attempts=orm.max_attempts,
            celery_task_id=orm.celery_task_id,
            payload=AsyncTaskPayload.from_dict(orm.payload_json),
            result=orm.result_json,
            error_category=orm.error_category,
            failure_reason=orm.failure_reason,
            created_at=orm.created_at,
            queued_at=orm.queued_at,
            started_at=orm.started_at,
            heartbeat_at=orm.heartbeat_at,
            completed_at=orm.completed_at,
        )

    async def get_or_create_task(
        self,
        idempotency_key: str,
        payload: AsyncTaskPayload,
        causation_id: str | None = None,
        max_attempts: int = 3,
    ) -> AsyncTask:
        """
        Create a new task, or return the existing one if it already exists.
        (Idempotent).
        """
        existing = await self.task_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return self._to_domain(existing)

        now = datetime.datetime.now(datetime.UTC)
        orm = AsyncTaskORM(
            id=uuid.uuid4(),
            task_type=payload.task_type,
            task_version=payload.task_version,
            idempotency_key=idempotency_key,
            case_id=payload.case_id,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            actor_id=payload.actor_id,
            correlation_id=payload.correlation_id,
            causation_id=causation_id,
            status=AsyncTaskStatus.PENDING.value,
            attempt_count=0,
            max_attempts=max_attempts,
            payload_json=payload.to_dict(),
            created_at=now,
        )
        saved = await self.task_repo.append(orm)
        return self._to_domain(saved)

    async def get_task(self, task_id: uuid.UUID) -> AsyncTask | None:
        """Get a task by ID."""
        orm = await self.task_repo.get_by_id(task_id)
        if orm:
            return self._to_domain(orm)
        return None

    async def transition_status(
        self, task_id: uuid.UUID, to_status: AsyncTaskStatus
    ) -> AsyncTask | None:
        """
        Transition task status, enforcing the state machine.
        """
        orm = await self.task_repo.get_by_id(task_id)
        if not orm:
            return None

        TaskStateMachine.validate_transition(orm.status, to_status)

        await self.task_repo.update_status(task_id, to_status)
        orm.status = to_status.value
        return self._to_domain(orm)

    async def record_heartbeat(self, task_id: uuid.UUID) -> None:
        """Record a heartbeat for a running task."""
        await self.task_repo.update_heartbeat(task_id)

    async def sweep_stale_tasks(self, stale_threshold_seconds: int = 120) -> list[uuid.UUID]:
        """
        Find RUNNING tasks older than the threshold, and transition them to PENDING
        or FAILED (if max attempts reached).
        """
        threshold = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=stale_threshold_seconds)
        stale_orms = await self.task_repo.find_stale_tasks(threshold)

        recovered_ids = []
        for orm in stale_orms:
            try:
                # If we have attempts remaining, retry from PENDING. Otherwise FAIL.
                if orm.attempt_count < orm.max_attempts:
                    TaskStateMachine.validate_transition(orm.status, AsyncTaskStatus.PENDING)
                    await self.task_repo.update_status(orm.id, AsyncTaskStatus.PENDING)
                else:
                    TaskStateMachine.validate_transition(orm.status, AsyncTaskStatus.FAILED)
                    await self.task_repo.update_status(orm.id, AsyncTaskStatus.FAILED)
                recovered_ids.append(orm.id)
            except InvalidTransitionError:
                # Log or handle? State mismatch. Skip.
                continue

        return recovered_ids
