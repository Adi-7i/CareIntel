"""
Thin AI Tasks.
"""

import asyncio
import uuid

from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger

from careintel.application.workflow.task_service import AsyncTaskService
from careintel.core.errors import ServiceUnavailableError
from careintel.domain.workflow.task_states import AsyncTaskStatus
from careintel.persistence.repositories.task_repo import AsyncTaskRepository
from careintel.workers.celery_app import celery_app
from careintel.workers.context import setup_worker_context
from careintel.workers.db import get_session_factory

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="careintel.tasks.ai.run_ai",
    autoretry_for=(ServiceUnavailableError, TimeoutError),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def run_ai(self, task_id: str) -> None:
    """Run AI for a case."""
    asyncio.run(_async_run_ai(self, task_id))


async def _async_run_ai(celery_task, task_id_str: str) -> None:
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
            with setup_worker_context(task.correlation_id, str(task.actor_id)) as actor:
                logger.info(f"Executing AI task {task_id} for case {task.case_id}")
                await asyncio.sleep(0.5)

        async with session_factory() as session:
            task_repo = AsyncTaskRepository(session)
            task_service = AsyncTaskService(task_repo)
            await task_service.transition_status(task_id, AsyncTaskStatus.SUCCEEDED)
            await session.commit()

    except SoftTimeLimitExceeded:
        async with session_factory() as session:
            task_repo = AsyncTaskRepository(session)
            task_service = AsyncTaskService(task_repo)
            await task_service.transition_status(task_id, AsyncTaskStatus.FAILED)
            await session.commit()
        raise
    except Exception as e:
        logger.exception(f"AI task {task_id} failed: {e}")
        raise
