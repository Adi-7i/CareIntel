from __future__ import annotations

import datetime
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from careintel.application.workflow.task_service import AsyncTaskService
from careintel.domain.workflow.models import AsyncTaskPayload
from careintel.domain.workflow.task_states import AsyncTaskStatus
from careintel.persistence.repositories.task_repo import AsyncTaskRepository


def _payload() -> AsyncTaskPayload:
    return AsyncTaskPayload(
        task_type="synthetic.task",
        task_version=1,
        entity_type="case",
        entity_id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        correlation_id="synthetic-correlation",
        config={},
    )


def _orm(payload: AsyncTaskPayload, *, attempts: int = 0, maximum: int = 3) -> SimpleNamespace:
    now = datetime.datetime.now(datetime.UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        task_type=payload.task_type,
        task_version=payload.task_version,
        idempotency_key="synthetic-key",
        case_id=payload.case_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        actor_id=payload.actor_id,
        correlation_id=payload.correlation_id,
        causation_id=None,
        status=AsyncTaskStatus.RUNNING.value,
        attempt_count=attempts,
        max_attempts=maximum,
        celery_task_id=None,
        payload_json=payload.to_dict(),
        result_json=None,
        error_category=None,
        failure_reason=None,
        created_at=now,
        queued_at=now,
        started_at=now,
        heartbeat_at=now,
        completed_at=None,
    )


@pytest.mark.unit
async def test_duplicate_idempotency_key_returns_existing_task() -> None:
    payload = _payload()
    existing = _orm(payload)
    repo = AsyncMock(spec=AsyncTaskRepository)
    repo.get_by_idempotency_key.return_value = existing
    service = AsyncTaskService(repo)

    result = await service.get_or_create_task("synthetic-key", payload)

    assert result.id == existing.id
    repo.append.assert_not_awaited()


@pytest.mark.unit
async def test_stale_task_with_attempts_remaining_returns_to_pending() -> None:
    payload = _payload()
    stale = _orm(payload, attempts=1, maximum=3)
    repo = AsyncMock(spec=AsyncTaskRepository)
    repo.find_stale_tasks.return_value = [stale]
    service = AsyncTaskService(repo)

    recovered = await service.sweep_stale_tasks(120)

    assert recovered == [stale.id]
    repo.update_status.assert_awaited_once_with(stale.id, AsyncTaskStatus.PENDING)


@pytest.mark.unit
async def test_stale_task_at_retry_limit_becomes_failed() -> None:
    payload = _payload()
    stale = _orm(payload, attempts=3, maximum=3)
    repo = AsyncMock(spec=AsyncTaskRepository)
    repo.find_stale_tasks.return_value = [stale]
    service = AsyncTaskService(repo)

    recovered = await service.sweep_stale_tasks(120)

    assert recovered == [stale.id]
    repo.update_status.assert_awaited_once_with(stale.id, AsyncTaskStatus.FAILED)
