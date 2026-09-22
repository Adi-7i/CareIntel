"""
Thin Processing Tasks.
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


# The task is a synchronous wrapper around an async function
@celery_app.task(
    bind=True,
    name="careintel.tasks.processing.run_processing",
    autoretry_for=(ServiceUnavailableError, TimeoutError),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def run_processing(self: Any, task_id: str) -> None:
    """Run processing for an evidence."""
    asyncio.run(_async_run_processing(task_id))


async def _async_run_processing(task_id_str: str) -> None:
    task_id = uuid.UUID(task_id_str)
    session_factory = get_session_factory()

    async with session_factory() as session:
        task_repo = AsyncTaskRepository(session)
        task_service = AsyncTaskService(task_repo)

        # 1. Load task and check idempotency
        task = await task_service.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found.")
            return

        if task.status in (AsyncTaskStatus.SUCCEEDED, AsyncTaskStatus.CANCELLED):
            logger.info(f"Task {task_id} already completed (status: {task.status}).")
            return

        # 2. Transition to RUNNING
        await task_service.transition_status(task_id, AsyncTaskStatus.RUNNING)
        await session.commit()

    # Run the actual work in a fresh session to keep transactions short
    try:
        async with session_factory() as session:
            # We would instantiate ProcessingService and its dependencies here.
            # For brevity in this skeleton, we assume we can build the service.
            # In a real app, a DI container or explicit builder function is used.
            # builder = ProcessingServiceBuilder(session)
            # svc = builder.build()

            # Context setup
            with setup_worker_context(task.correlation_id, str(task.actor_id)):
                raise CapabilityNotImplementedError(
                    "Processing worker execution is not wired to the application service."
                )

    except SoftTimeLimitExceeded:
        logger.error(f"Task {task_id} exceeded time limit.")
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
        logger.error("Processing task failed", extra={"error_type": type(exc).__name__})
        raise
