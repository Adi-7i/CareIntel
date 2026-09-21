"""
Thin Workflow Tasks.
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
    name="careintel.tasks.workflow.advance_case",
    autoretry_for=(ServiceUnavailableError, TimeoutError),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def advance_case(self, task_id: str) -> None:
    """Advance case state."""
    asyncio.run(_async_advance_case(self, task_id))


async def _async_advance_case(celery_task, task_id_str: str) -> None:
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
                logger.info(f"Executing case advance task {task_id} for case {task.case_id}")
                await asyncio.sleep(0.1)

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
        logger.exception(f"Case advance task {task_id} failed: {e}")
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
def trigger_structuring(self, task_id: str) -> None:
    """Trigger structuring phase."""
    asyncio.run(_async_trigger_structuring(self, task_id))


async def _async_trigger_structuring(celery_task, task_id_str: str) -> None:
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
                logger.info(f"Executing trigger structuring task {task_id} for case {task.case_id}")
                await asyncio.sleep(0.1)

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
        logger.exception(f"Trigger structuring task {task_id} failed: {e}")
        raise


@celery_app.task(
    bind=True,
    name="careintel.tasks.workflow.recover_stale_tasks",
    autoretry_for=(ServiceUnavailableError,),
    retry_kwargs={"max_retries": 2},
)
def recover_stale_tasks(self, threshold_seconds: int = 120) -> None:
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
                logger.info(f"Recovered stale tasks: {recovered_ids}")
            await session.commit()
    except Exception as e:
        logger.exception(f"Stale task recovery failed: {e}")
        raise
