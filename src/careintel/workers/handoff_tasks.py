"""Celery adapter for configured referral delivery."""

from __future__ import annotations

import asyncio
from typing import Any

from careintel.core.config import Environment, get_settings
from careintel.core.errors import ServiceUnavailableError
from careintel.domain.workflow.models import AsyncTask
from careintel.infrastructure.handoff.demo import DemoHandoffProvider
from careintel.persistence.repositories.handoff_repo import HandoffRepository
from careintel.workers.celery_app import celery_app
from careintel.workers.executor import RetryableTaskError, execute_durable_task
from careintel.workers.services import build_handoff_service


async def _handle_handoff(session: Any, task: AsyncTask, actor: Any) -> dict[str, object]:
    del actor
    service = build_handoff_service(session)
    handoff = await service.begin_delivery(task.entity_id)
    package = await HandoffRepository(session).get_referral_package(handoff.referral_package_id)
    recipient = await HandoffRepository(session).get_recipient(handoff.recipient_id)
    if package is None or recipient is None:
        raise ServiceUnavailableError("Handoff dependencies are unavailable.")
    await session.commit()

    provider_name = str(recipient.config_json.get("provider", ""))
    settings = get_settings()
    reference: str | None
    failure_reason: str | None
    if provider_name != "demo" or settings.app_env == Environment.PRODUCTION:
        result_success = False
        reference = None
        failure_reason = "HandoffProviderUnavailable"
    else:
        result = await DemoHandoffProvider().deliver(package.content_json, recipient.config_json)
        result_success = result.success
        reference = result.reference
        failure_reason = result.failure_reason

    updated = await service.record_delivery_result(
        handoff.id,
        result_success,
        reference,
        failure_reason,
        task.correlation_id,
    )
    if not result_success:
        await session.commit()
        raise ServiceUnavailableError("Configured handoff provider did not deliver.")
    return {
        "handoff_id": str(updated.id),
        "status": updated.status,
        "delivery_reference_recorded": bool(updated.delivery_reference),
    }


@celery_app.task(
    bind=True,
    name="careintel.tasks.handoff.deliver_handoff",
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def deliver_handoff(self: Any, task_id: str) -> dict[str, object] | None:
    try:
        return asyncio.run(
            execute_durable_task(task_id, _handle_handoff, celery_task_id=self.request.id)
        )
    except RetryableTaskError as exc:
        raise self.retry(exc=exc) from exc
