"""Celery adapter for persisted case-scoped retrieval commands."""

from __future__ import annotations

import asyncio
from typing import Any

from careintel.domain.retrieval.status import SearchMode
from careintel.domain.workflow.models import AsyncTask
from careintel.workers.celery_app import celery_app
from careintel.workers.executor import RetryableTaskError, execute_durable_task
from careintel.workers.services import build_retrieval_service


async def _handle_retrieval(session: Any, task: AsyncTask, actor: Any) -> dict[str, object]:
    config = task.payload.config
    service = await build_retrieval_service(session)
    result = await service.retrieve_knowledge(
        actor,
        task.case_id,
        str(config["query"]),
        str(config["corpus_version"]),
        SearchMode(str(config.get("search_mode", SearchMode.HYBRID.value))),
        int(config.get("top_k", 10)),
    )
    return {
        "retrieval_run_id": str(result.metadata.retrieval_run_id),
        "status": result.metadata.status.value,
        "candidate_count": result.metadata.candidate_count,
    }


@celery_app.task(
    bind=True,
    name="careintel.tasks.retrieval.run_retrieval",
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def run_retrieval(self: Any, task_id: str) -> dict[str, object] | None:
    try:
        return asyncio.run(
            execute_durable_task(task_id, _handle_retrieval, celery_task_id=self.request.id)
        )
    except RetryableTaskError as exc:
        raise self.retry(exc=exc) from exc
