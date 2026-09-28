"""Celery adapters for explicit workflow transitions and recovery."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from careintel.application.workflow.outbox_dispatcher import UnifiedOutboxDispatcher
from careintel.application.workflow.task_service import AsyncTaskService
from careintel.domain.audit.events import AuditEventType
from careintel.domain.case.commands import TransitionCaseCommand
from careintel.domain.case.states import CaseState
from careintel.domain.workflow.models import AsyncTask
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.repositories.task_repo import AsyncTaskRepository
from careintel.workers.celery_app import celery_app
from careintel.workers.db import get_session_factory
from careintel.workers.executor import RetryableTaskError, execute_durable_task
from careintel.workers.services import build_case_service, build_structuring_service


async def _handle_advance_case(session: Any, task: AsyncTask, actor: Any) -> dict[str, object]:
    config = task.payload.config
    case = await build_case_service(session).transition_state(
        TransitionCaseCommand(
            case_id=task.case_id,
            actor_id=actor.id,
            from_state=CaseState(str(config["from_state"])),
            to_state=CaseState(str(config["to_state"])),
            expected_version=int(config["expected_version"]),
            reason=str(config.get("reason") or "Explicit asynchronous workflow command"),
            correlation_id=task.correlation_id,
        ),
        actor,
    )
    return {"case_id": str(case.case_id), "state": case.state.value, "version": case.version}


async def _handle_structuring(session: Any, task: AsyncTask, actor: Any) -> dict[str, object]:
    result = await build_structuring_service(session).evaluate_case(
        actor,
        task.case_id,
        uuid.UUID(str(task.payload.config["extraction_run_id"])),
        task.correlation_id,
    )
    return {
        "structuring_run_id": str(result.run_id),
        "status": result.status,
        "timeline_count": result.timeline_count,
        "missing_info_count": result.missing_info_count,
    }


def _run(self: Any, task_id: str, handler: Any) -> dict[str, object] | None:
    try:
        return asyncio.run(execute_durable_task(task_id, handler, celery_task_id=self.request.id))
    except RetryableTaskError as exc:
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, name="careintel.tasks.workflow.advance_case", max_retries=3)
def advance_case(self: Any, task_id: str) -> dict[str, object] | None:
    return _run(self, task_id, _handle_advance_case)


@celery_app.task(bind=True, name="careintel.tasks.workflow.trigger_structuring", max_retries=3)
def trigger_structuring(self: Any, task_id: str) -> dict[str, object] | None:
    return _run(self, task_id, _handle_structuring)


@celery_app.task(bind=True, name="careintel.tasks.workflow.recover_stale_tasks", max_retries=2)
def recover_stale_tasks(self: Any, threshold_seconds: int = 120) -> int:
    return asyncio.run(_recover_stale_tasks(threshold_seconds))


async def _recover_stale_tasks(threshold_seconds: int) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = AsyncTaskService(AsyncTaskRepository(session))
        recovered_ids = await service.sweep_stale_tasks(threshold_seconds)
        for task_id in recovered_ids:
            task = await service.get_task(task_id)
            if task is None:
                continue
            session.add(
                AuditLogORM(
                    event_type=AuditEventType.TASK_STALE_RECOVERED.value,
                    actor_id=task.actor_id,
                    target_id=task.id,
                    target_type="async_task",
                    correlation_id=task.correlation_id,
                    outcome="SUCCESS" if task.status.value == "PENDING" else "FAILURE",
                    detail={"status": task.status.value},
                )
            )
        await session.commit()

    republished = 0
    async with session_factory() as session:
        service = AsyncTaskService(AsyncTaskRepository(session))
        for task_id in recovered_ids:
            task = await service.get_task(task_id)
            if task is None or task.status.value != "PENDING":
                continue
            celery_app.send_task(
                task.task_type,
                kwargs={"task_id": str(task.id)},
                task_id=str(task.id),
                queue=UnifiedOutboxDispatcher._route_task(task.task_type),
            )
            await AsyncTaskRepository(session).set_queued(task.id, str(task.id))
            republished += 1
        await session.commit()
    return republished
