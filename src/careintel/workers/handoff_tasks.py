"""
Celery tasks for Handoff processing (Phase 9).
"""

import asyncio
import logging
import uuid
from typing import Any

from careintel.core.errors import CapabilityNotImplementedError
from careintel.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


# Normally we'd use a dependency injection container here,
# but for Celery tasks we'll instantiate what we need.
async def _execute_handoff_delivery(handoff_id: uuid.UUID, correlation_id: str) -> None:
    del handoff_id, correlation_id
    raise CapabilityNotImplementedError(
        "Handoff delivery has no configured production provider and is disabled."
    )


@celery_app.task(
    name="careintel.tasks.handoff.deliver_handoff",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def deliver_handoff_task(self: Any, payload: dict[str, Any]) -> None:
    """
    Celery task to deliver a handoff.
    Payload expected: {"handoff_id": "uuid", "correlation_id": "str"}
    """
    handoff_id = uuid.UUID(payload["handoff_id"])
    correlation_id = payload.get("correlation_id", "unknown")

    logger.info(
        "Starting handoff delivery for %s", handoff_id, extra={"correlation_id": correlation_id}
    )

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_execute_handoff_delivery(handoff_id, correlation_id))
    except Exception as exc:
        logger.warning("Handoff delivery failed, scheduling retry.", exc_info=True)
        raise self.retry(exc=exc) from exc
