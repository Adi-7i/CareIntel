"""
Unified Outbox Dispatcher.
"""

import asyncio
import datetime
import logging
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.workflow.task_service import AsyncTaskService
from careintel.domain.workflow.models import AsyncTaskPayload
from careintel.persistence.models.case import CaseOutboxORM
from careintel.persistence.models.evidence import EvidenceOutboxORM
from careintel.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class UnifiedOutboxDispatcher:
    """
    Polls outbox tables, creates AsyncTasks, and dispatches to Celery.
    """

    def __init__(self, session_factory: Any, task_service: AsyncTaskService) -> None:
        # We need a session factory because the dispatcher runs in a loop
        # and should create fresh short-lived sessions.
        self.session_factory = session_factory
        self.task_service = task_service

    async def _process_batch(self, session: AsyncSession, model_cls: Any, batch_size: int = 50) -> int:
        """Process a single batch of events for a given outbox model."""
        # 1. Select unpublished with SKIP LOCKED
        stmt = (
            select(model_cls)
            .where(model_cls.published_at.is_(None))
            .order_by(model_cls.id)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        events: Sequence[Any] = result.scalars().all()

        if not events:
            return 0

        processed = 0
        now = datetime.datetime.now(datetime.UTC)

        for event in events:
            try:
                # 2. Map event to TaskPayload
                # We do this based on the event_type mapping to a Celery task.
                task_name = self._map_event_to_task_name(event.event_type)
                
                if not task_name:
                    # Not all events trigger async tasks.
                    # Just mark as published and skip task creation.
                    event.published_at = now
                    processed += 1
                    continue
                
                payload = self._build_payload(event, task_name)
                
                # 3. Idempotently create task
                task = await self.task_service.get_or_create_task(
                    idempotency_key=f"outbox_{event.id}",
                    payload=payload,
                    causation_id=event.id
                )
                
                # 4. Dispatch to Celery
                celery_app.send_task(
                    task_name,
                    kwargs={"task_id": str(task.id)},
                    queue=self._route_task(task_name),
                )
                
                # 5. Mark outbox published & task queued
                event.published_at = now
                await self.task_service.transition_status(task.id, "QUEUED")
                
                processed += 1
            except Exception as e:
                logger.exception(f"Failed to process outbox event {event.id}: {e}")
                # We don't rollback the whole batch, we just leave this event unpublished
                # so it will be retried. But we do need to rollback the session to clear the error state.
                raise e

        # Commit batch
        await session.commit()
        return processed

    def _map_event_to_task_name(self, event_type: str) -> str | None:
        """Map a domain event to a Celery task name."""
        mapping = {
            "EVIDENCE_PROCESSING_REQUESTED": "careintel.tasks.processing.run_processing",
            "PROCESSING_COMPLETED": "careintel.tasks.workflow.advance_case",
            "EXTRACTION_COMPLETED": "careintel.tasks.workflow.trigger_structuring",
            "RETRIEVAL_REQUESTED": "careintel.tasks.retrieval.run_retrieval",
            "AI_RUN_REQUESTED": "careintel.tasks.ai.run_ai",
            "CASE_WORKFLOW_ADVANCE": "careintel.tasks.workflow.advance_case",
        }
        return mapping.get(event_type)

    def _build_payload(self, event: Any, task_name: str) -> AsyncTaskPayload:
        """Construct the payload for the async task."""
        # Determine entity type
        if isinstance(event, CaseOutboxORM):
            entity_type = "case"
            entity_id = event.case_id
        else:
            entity_type = "evidence"
            entity_id = getattr(event, "evidence_id", event.case_id) # Evidence outbox has evidence_id

        # The config is typically the payload from the outbox
        config = event.payload

        return AsyncTaskPayload(
            task_type=task_name,
            task_version=1,
            entity_type=entity_type,
            entity_id=entity_id,
            case_id=event.case_id,
            actor_id=event.actor_id,
            correlation_id=event.correlation_id,
            config=config,
        )

    def _route_task(self, task_name: str) -> str:
        """Determine Celery queue for task."""
        if "processing." in task_name:
            return "careintel_processing"
        elif "ai." in task_name:
            return "careintel_ai"
        elif "retrieval." in task_name:
            return "careintel_retrieval"
        else:
            return "careintel_workflow"

    async def poll_forever(self, interval_seconds: float = 2.0) -> None:
        """Run the polling loop indefinitely."""
        logger.info("Outbox Dispatcher starting polling loop.")
        
        loops_since_sweep = 0
        
        while True:
            try:
                # Use a fresh session for each iteration
                async with self.session_factory() as session:
                    case_processed = await self._process_batch(session, CaseOutboxORM)
                    evidence_processed = await self._process_batch(session, EvidenceOutboxORM)
                    
                    if case_processed > 0 or evidence_processed > 0:
                        logger.debug(f"Dispatched {case_processed} case events, {evidence_processed} evidence events.")
                
                # Periodically trigger stale sweep (e.g. every 60 seconds)
                loops_since_sweep += 1
                if loops_since_sweep * interval_seconds >= 60:
                    celery_app.send_task(
                        "careintel.tasks.workflow.recover_stale_tasks",
                        kwargs={"threshold_seconds": 120},
                        queue="careintel_workflow"
                    )
                    loops_since_sweep = 0

            except Exception as e:
                logger.error(f"Outbox polling error: {e}")
                # Sleep a bit longer on error
                await asyncio.sleep(interval_seconds * 2)
                continue

            await asyncio.sleep(interval_seconds)
