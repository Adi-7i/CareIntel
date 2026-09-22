"""
Thin Workflow Tasks.
"""

import asyncio
import uuid
from typing import Any

from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger

from careintel.application.workflow.task_service import AsyncTaskService
from careintel.core.errors import CapabilityNotImplementedError, ServiceUnavailableError
from careintel.domain.workflow.task_states import AsyncTaskStatus
from careintel.persistence.repositories.task_repo import AsyncTaskRepository
from careintel.workers.celery_app import celery_app
from careintel.workers.context import setup_worker_context
from careintel.workers.db import get_session_factory

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="careintel.tasks.workflow.advance_case",
    autoretry_for=(ServiceUnavailableError, TimeoutError),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def advance_case(self: Any, task_id: str) -> None:
    """Advance case state."""
    asyncio.run(_async_advance_case(task_id))


async def _async_advance_case(task_id_str: str) -> None:
    task_id = uuid.UUID(task_id_str)
    session_factory = get_session_factory()

    async with session_factory() as session:
        task_repo = AsyncTaskRepository(session)
        task_service = AsyncTaskService(task_repo)

        task = await task_service.get_task(task_id)
        if not task:
            return

        if task.status in (AsyncTaskStatus.SUCCEEDED, AsyncTaskStatus.CANCELLED):
            return

        await task_service.transition_status(task_id, AsyncTaskStatus.RUNNING)
        await session.commit()

    try:
        async with session_factory() as session:
            with setup_worker_context(task.correlation_id, str(task.actor_id)):
                raise CapabilityNotImplementedError(
                    "Case-advance worker execution is not wired to the application service."
                )

    except SoftTimeLimitExceeded:
        async with session_factory() as session:
            task_repo = AsyncTaskRepository(session)
            task_service = AsyncTaskService(task_repo)
            await task_service.transition_status(task_id, AsyncTaskStatus.FAILED)
            await session.commit()
        raise
    except Exception as exc:
        async with session_factory() as session:
            task_service = AsyncTaskService(AsyncTaskRepository(session))
            await task_service.transition_status(task_id, AsyncTaskStatus.FAILED)
            await session.commit()
        logger.error("Case advance task failed", extra={"error_type": type(exc).__name__})
        raise


@celery_app.task(
    bind=True,
    name="careintel.tasks.workflow.trigger_structuring",
    autoretry_for=(ServiceUnavailableError, TimeoutError),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def trigger_structuring(self: Any, task_id: str) -> None:
    """Trigger structuring phase."""
    asyncio.run(_async_trigger_structuring(task_id))


async def _async_trigger_structuring(task_id_str: str) -> None:
    task_id = uuid.UUID(task_id_str)
    session_factory = get_session_factory()

    async with session_factory() as session:
        task_repo = AsyncTaskRepository(session)
        task_service = AsyncTaskService(task_repo)

        task = await task_service.get_task(task_id)
        if not task:
            return
        if task.status in (AsyncTaskStatus.SUCCEEDED, AsyncTaskStatus.CANCELLED):
            return
        await task_service.transition_status(task_id, AsyncTaskStatus.RUNNING)
        await session.commit()

    try:
        async with session_factory() as session:
            with setup_worker_context(task.correlation_id, str(task.actor_id)):
                raise CapabilityNotImplementedError(
                    "Structuring worker execution is not wired to the application service."
                )
    except SoftTimeLimitExceeded:
        async with session_factory() as session:
            task_repo = AsyncTaskRepository(session)
            task_service = AsyncTaskService(task_repo)
            await task_service.transition_status(task_id, AsyncTaskStatus.FAILED)
            await session.commit()
        raise
    except Exception as exc:
        async with session_factory() as session:
            task_service = AsyncTaskService(AsyncTaskRepository(session))
            await task_service.transition_status(task_id, AsyncTaskStatus.FAILED)
            await session.commit()
        logger.error("Structuring task failed", extra={"error_type": type(exc).__name__})
        raise


@celery_app.task(
    bind=True,
    name="careintel.tasks.workflow.recover_stale_tasks",
    autoretry_for=(ServiceUnavailableError,),
    retry_kwargs={"max_retries": 2},
)
def recover_stale_tasks(self: Any, threshold_seconds: int = 120) -> None:
    """Sweep and recover stale tasks."""
    asyncio.run(_async_recover_stale_tasks(threshold_seconds))


async def _async_recover_stale_tasks(threshold_seconds: int) -> None:
    session_factory = get_session_factory()
    try:
        async with session_factory() as session:
            task_repo = AsyncTaskRepository(session)
            task_service = AsyncTaskService(task_repo)

            recovered_ids = await task_service.sweep_stale_tasks(threshold_seconds)
            if recovered_ids:
                logger.info("Recovered stale tasks", extra={"recovered_count": len(recovered_ids)})
            await session.commit()
    except Exception as exc:
        logger.error("Stale task recovery failed", extra={"error_type": type(exc).__name__})
        raise
