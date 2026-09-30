"""Celery adapter for persisted evidence-processing commands."""

from __future__ import annotations

import asyncio
from typing import Any

from careintel.core.errors import ServiceUnavailableError, ValidationError
from careintel.domain.processing.processing_commands import TriggerProcessingCommand
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.processing.processor_type import ProcessorType
from careintel.domain.workflow.models import AsyncTask
from careintel.workers.celery_app import celery_app
from careintel.workers.executor import RetryableTaskError, execute_durable_task
from careintel.workers.services import build_processing_service


async def _handle_processing(session: Any, task: AsyncTask, actor: Any) -> dict[str, object]:
    processor_type = ProcessorType(str(task.payload.config["processor_type"]))
    service = await build_processing_service(session)
    result = await service.execute_processing(
        TriggerProcessingCommand(
            evidence_id=task.entity_id,
            processor_type=processor_type,
            parameters=dict(task.payload.config),
        ),
        actor,
        task.correlation_id,
    )
    if result.status == ProcessingStatus.FAILED:
        transient_names = {
            "AzureError",
            "ClientConnectionError",
            "HttpResponseError",
            "ServiceRequestError",
            "StorageError",
            "TimeoutError",
        }
        if result.failure_reason in transient_names:
            raise ServiceUnavailableError("Processing provider failed transiently.")
        raise ValidationError("Processing failed permanently.")
    return {"processing_run_id": str(result.run_id), "status": result.status.value}


@celery_app.task(
    bind=True,
    name="careintel.tasks.processing.run_processing",
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def run_processing(self: Any, task_id: str) -> dict[str, object] | None:
    try:
        return asyncio.run(
            execute_durable_task(task_id, _handle_processing, celery_task_id=self.request.id)
        )
    except RetryableTaskError as exc:
        raise self.retry(exc=exc) from exc
