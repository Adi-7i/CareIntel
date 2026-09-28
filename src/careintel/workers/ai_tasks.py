"""Celery adapter for persisted advisory-AI commands."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from careintel.domain.ai.status import TaskType
from careintel.domain.workflow.models import AsyncTask
from careintel.workers.celery_app import celery_app
from careintel.workers.executor import RetryableTaskError, execute_durable_task
from careintel.workers.services import build_ai_workflow_service


async def _handle_ai(session: Any, task: AsyncTask, actor: Any) -> dict[str, object]:
    config = task.payload.config
    service = await build_ai_workflow_service(session)
    draft = await service.execute_advisory(
        actor,
        task.case_id,
        uuid.UUID(str(config["retrieval_run_id"])),
        TaskType(str(config["task_type"])),
    )
    return {
        "draft_id": str(draft.draft_id),
        "reviewer_status": draft.reviewer_status.value,
        "validation_status": draft.validation_status.value,
    }


@celery_app.task(
    bind=True,
    name="careintel.tasks.ai.run_ai",
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def run_ai(self: Any, task_id: str) -> dict[str, object] | None:
    try:
        return asyncio.run(
            execute_durable_task(task_id, _handle_ai, celery_task_id=self.request.id)
        )
    except RetryableTaskError as exc:
        raise self.retry(exc=exc) from exc
