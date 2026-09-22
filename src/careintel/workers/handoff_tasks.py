"""
Celery tasks for Handoff processing (Phase 9).
"""

import asyncio
import logging
import uuid
from typing import Any

from careintel.domain.handoff.states import HandoffStatus
from careintel.infrastructure.handoff.demo import DemoHandoffProvider
from careintel.persistence.database import session_maker
from careintel.persistence.repositories.handoff_repo import HandoffRepository
from careintel.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


# Normally we'd use a dependency injection container here,
# but for Celery tasks we'll instantiate what we need.
async def _execute_handoff_delivery(handoff_id: uuid.UUID, correlation_id: str) -> None:
    async with session_maker() as session:
        handoff_repo = HandoffRepository(session)

        # 1. Fetch Handoff
        handoff = await handoff_repo.get_handoff(handoff_id)
        if not handoff:
            logger.error("Handoff %s not found.", handoff_id)
            return

        if handoff.status != HandoffStatus.SENDING.value:
             logger.info("Handoff %s is not in SENDING state (is %s). Skipping.", handoff_id, handoff.status)
             return

        # 2. Fetch dependencies
        package = await handoff_repo.get_referral_package(handoff.referral_package_id)
        if not package:
            logger.error("Package %s not found for handoff %s.", handoff.referral_package_id, handoff_id)
            return

        recipient = await handoff_repo.get_recipient(handoff.recipient_id)
        if not recipient:
            logger.error("Recipient %s not found for handoff %s.", handoff.recipient_id, handoff_id)
            return

        # 3. Delivery (using Demo provider for now)
        provider = DemoHandoffProvider()

        try:
             result = await provider.deliver(package.content_json, recipient.config_json)

             # Instead of updating directly here, we could just rely on Phase 8's
             # outbox task result handling, but since this is specific to handoff delivery,
             # we use the HandoffService to record the result in a real setup.
             # For the sake of this task worker, we'll manually update via repo for simplicity,
             # or we would instantiate HandoffService here.

             # But the prompt requested we write this using HandoffService.
             from careintel.application.handoff.handoff_service import HandoffService
             from careintel.persistence.repositories.audit_repo import AuditRepository
             from careintel.persistence.repositories.case_repo import CaseRepository

             case_repo = CaseRepository(session)
             audit_repo = AuditRepository(session)
             handoff_service = HandoffService(handoff_repo, case_repo, audit_repo)

             await handoff_service.record_delivery_result(
                 handoff_id=handoff_id,
                 success=result.success,
                 reference=result.reference,
                 failure_reason=result.failure_reason,
                 correlation_id=correlation_id
             )

             await session.commit()
             logger.info("Handoff %s delivery recorded.", handoff_id)

        except Exception:
             logger.exception("Failed to deliver handoff %s.", handoff_id)
             await session.rollback()
             raise


@celery_app.task(
    name="careintel.tasks.handoff.deliver_handoff",
    bind=True,
    max_retries=3,
    default_retry_delay=60, # 1 minute
)
def deliver_handoff_task(self: Any, payload: dict[str, Any]) -> None:
    """
    Celery task to deliver a handoff.
    Payload expected: {"handoff_id": "uuid", "correlation_id": "str"}
    """
    handoff_id = uuid.UUID(payload["handoff_id"])
    correlation_id = payload.get("correlation_id", "unknown")

    logger.info("Starting handoff delivery for %s", handoff_id, extra={"correlation_id": correlation_id})

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_execute_handoff_delivery(handoff_id, correlation_id))
    except Exception as exc:
        logger.warning("Handoff delivery failed, scheduling retry.", exc_info=True)
        raise self.retry(exc=exc)
