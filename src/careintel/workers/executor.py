"""Shared durable execution boundary for Celery business tasks."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.workflow.task_service import AsyncTaskService
from careintel.core.errors import ServiceUnavailableError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.workflow.models import AsyncTask
from careintel.infrastructure.ai.port import LLMProviderError
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.repositories.task_repo import AsyncTaskRepository
from careintel.workers.context import load_worker_actor, setup_worker_context
from careintel.workers.db import get_session_factory

TaskHandler = Callable[[AsyncSession, AsyncTask, UserContext], Awaitable[dict[str, object]]]


class RetryableTaskError(Exception):
    """Sanitized marker consumed by the Celery wrapper."""


class PermanentTaskError(Exception):
    """Sanitized marker used to prevent unsafe automatic retries."""


def is_transient_failure(exc: Exception) -> bool:
    if isinstance(
        exc,
        (
            ServiceUnavailableError,
            TimeoutError,
            ConnectionError,
            SoftTimeLimitExceeded,
            OperationalError,
            LLMProviderError,
        ),
    ):
        return True
    return type(exc).__module__.split(".", maxsplit=1)[0] in {
        "azure",
        "httpcore",
        "httpx",
        "openai",
        "redis",
        "kombu",
    }


async def _append_task_audit(
    session: AsyncSession,
    task: AsyncTask,
    event_type: AuditEventType,
    outcome: str,
    detail: dict[str, object] | None = None,
) -> None:
    session.add(
        AuditLogORM(
            event_type=event_type.value,
            actor_id=task.actor_id,
            target_id=task.id,
            target_type="async_task",
            correlation_id=task.correlation_id,
            outcome=outcome,
            detail=detail,
        )
    )


async def execute_durable_task(
    task_id_text: str,
    handler: TaskHandler,
    *,
    celery_task_id: str | None = None,
) -> dict[str, object] | None:
    """Claim once, run business work, and persist a truthful terminal/retry state."""
    task_id = uuid.UUID(task_id_text)
    session_factory = get_session_factory()

    async with session_factory() as session:
        task_service = AsyncTaskService(AsyncTaskRepository(session))
        task = await task_service.claim_for_execution(task_id, celery_task_id)
        if task is None:
            await session.rollback()
            return None
        await _append_task_audit(
            session,
            task,
            AuditEventType.TASK_STARTED,
            "SUCCESS",
            {"attempt": task.attempt_count, "task_type": task.task_type},
        )
        await session.commit()

    try:
        async with session_factory() as work_session:
            actor = await load_worker_actor(work_session, task.actor_id)
            with setup_worker_context(task.correlation_id, str(task.actor_id)):
                result = await handler(work_session, task, actor)
            await work_session.commit()
    except Exception as exc:
        transient = is_transient_failure(exc)
        exhausted = task.attempt_count >= task.max_attempts
        error_category = type(exc).__name__
        async with session_factory() as state_session:
            service = AsyncTaskService(AsyncTaskRepository(state_session))
            if transient and not exhausted:
                await service.record_retry(task.id, error_category, error_category)
                event = AuditEventType.TASK_RETRYING
                outcome = "RETRY"
            else:
                await service.record_failure(task.id, error_category, error_category)
                event = AuditEventType.TASK_FAILED
                outcome = "FAILURE"
            await _append_task_audit(
                state_session,
                task,
                event,
                outcome,
                {
                    "attempt": task.attempt_count,
                    "error_category": error_category,
                    "retry_exhausted": exhausted,
                },
            )
            await state_session.commit()
        if transient and not exhausted:
            raise RetryableTaskError(error_category) from None
        raise PermanentTaskError(error_category) from None

    async with session_factory() as state_session:
        service = AsyncTaskService(AsyncTaskRepository(state_session))
        await service.record_success(task.id, result)
        await _append_task_audit(
            state_session,
            task,
            AuditEventType.TASK_SUCCEEDED,
            "SUCCESS",
            {"attempt": task.attempt_count, "task_type": task.task_type},
        )
        await state_session.commit()
    return result
