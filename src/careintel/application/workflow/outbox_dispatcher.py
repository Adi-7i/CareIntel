"""Durable dispatcher for the existing case and evidence outboxes."""

from __future__ import annotations

import asyncio
import datetime
import logging
import socket
import uuid
from dataclasses import dataclass
from typing import Any, ClassVar

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.workflow.task_service import AsyncTaskService
from careintel.domain.audit.events import AuditEventType
from careintel.domain.workflow.models import AsyncTaskPayload
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseOutboxORM
from careintel.persistence.models.evidence import EvidenceOutboxORM
from careintel.persistence.repositories.task_repo import AsyncTaskRepository
from careintel.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class DispatchStatus:
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    RETRY = "RETRY"
    DISPATCHED = "DISPATCHED"
    FAILED = "FAILED"
    IGNORED = "IGNORED"


@dataclass(frozen=True)
class ClaimedDispatch:
    outbox_kind: str
    event_id: str
    task_id: uuid.UUID
    task_name: str
    queue: str


class UnifiedOutboxDispatcher:
    """Claims in PostgreSQL, commits, then publishes stable task IDs to Celery."""

    _TASK_MAP: ClassVar[dict[str, str]] = {
        "EVIDENCE_PROCESSING_REQUESTED": "careintel.tasks.processing.run_processing",
        "RETRIEVAL_REQUESTED": "careintel.tasks.retrieval.run_retrieval",
        "AI_RUN_REQUESTED": "careintel.tasks.ai.run_ai",
        "CASE_WORKFLOW_ADVANCE": "careintel.tasks.workflow.advance_case",
        "STRUCTURING_REQUESTED": "careintel.tasks.workflow.trigger_structuring",
        "HANDOFF_SEND_REQUESTED": "careintel.tasks.handoff.deliver_handoff",
    }
    _MODELS: ClassVar[dict[str, Any]] = {
        "case": CaseOutboxORM,
        "evidence": EvidenceOutboxORM,
    }

    def __init__(
        self,
        session_factory: Any,
        *,
        dispatcher_id: str | None = None,
        claim_timeout_seconds: int = 120,
    ) -> None:
        self.session_factory = session_factory
        self.dispatcher_id = dispatcher_id or f"{socket.gethostname()}-{uuid.uuid4()}"
        self.claim_timeout_seconds = claim_timeout_seconds

    @staticmethod
    def _now() -> datetime.datetime:
        return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    async def _claim_batch(
        self, session: AsyncSession, outbox_kind: str, batch_size: int
    ) -> list[ClaimedDispatch]:
        model_cls = self._MODELS[outbox_kind]
        now = self._now()
        stale_before = now - datetime.timedelta(seconds=self.claim_timeout_seconds)
        stmt = (
            select(model_cls)
            .where(
                model_cls.published_at.is_(None),
                model_cls.dispatch_attempts < model_cls.max_dispatch_attempts,
                or_(model_cls.next_attempt_at.is_(None), model_cls.next_attempt_at <= now),
                or_(
                    model_cls.dispatch_status.in_([DispatchStatus.PENDING, DispatchStatus.RETRY]),
                    (
                        (model_cls.dispatch_status == DispatchStatus.CLAIMED)
                        & (model_cls.claimed_at < stale_before)
                    ),
                ),
            )
            .order_by(model_cls.occurred_at, model_cls.id)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        events = list((await session.execute(stmt)).scalars().all())
        task_service = AsyncTaskService(AsyncTaskRepository(session))
        claimed: list[ClaimedDispatch] = []

        for event in events:
            task_name = self._TASK_MAP.get(event.event_type)
            if task_name is None:
                event.dispatch_status = DispatchStatus.FAILED
                event.dispatch_attempts = event.max_dispatch_attempts
                event.last_error_category = "UnsupportedEventType"
                event.claimed_at = None
                event.claimed_by = None
                continue
            if event.actor_id is None:
                event.dispatch_status = DispatchStatus.FAILED
                event.dispatch_attempts = event.max_dispatch_attempts
                event.last_error_category = "MissingActor"
                continue

            task = await task_service.get_or_create_task(
                idempotency_key=f"outbox_{event.id}",
                payload=self._build_payload(event, task_name),
                causation_id=event.id,
            )
            event.dispatch_status = DispatchStatus.CLAIMED
            event.dispatch_attempts += 1
            event.claimed_at = now
            event.claimed_by = self.dispatcher_id
            event.last_error_category = None
            event.celery_task_id = str(task.id)
            claimed.append(
                ClaimedDispatch(
                    outbox_kind=outbox_kind,
                    event_id=event.id,
                    task_id=task.id,
                    task_name=task_name,
                    queue=self._route_task(task_name),
                )
            )

        await session.commit()
        return claimed

    async def _record_dispatched(self, claimed: ClaimedDispatch) -> None:
        model_cls = self._MODELS[claimed.outbox_kind]
        async with self.session_factory() as session:
            event = (
                await session.execute(
                    select(model_cls).where(model_cls.id == claimed.event_id).with_for_update()
                )
            ).scalar_one_or_none()
            if event is None or event.published_at is not None:
                return
            now = self._now()
            event.dispatch_status = DispatchStatus.DISPATCHED
            event.published_at = now
            event.claimed_at = None
            event.claimed_by = None
            event.next_attempt_at = None
            await AsyncTaskRepository(session).set_queued(claimed.task_id, str(claimed.task_id))
            session.add(
                AuditLogORM(
                    event_type=AuditEventType.OUTBOX_DISPATCHED.value,
                    actor_id=event.actor_id,
                    target_id=claimed.task_id,
                    target_type="async_task",
                    correlation_id=event.correlation_id,
                    causation_id=event.id,
                    source="dispatcher",
                    outcome="SUCCESS",
                    detail={"event_type": event.event_type},
                )
            )
            await session.commit()

    async def _record_dispatch_failure(self, claimed: ClaimedDispatch, error_category: str) -> None:
        model_cls = self._MODELS[claimed.outbox_kind]
        async with self.session_factory() as session:
            event = (
                await session.execute(
                    select(model_cls).where(model_cls.id == claimed.event_id).with_for_update()
                )
            ).scalar_one_or_none()
            if event is None or event.published_at is not None:
                return
            exhausted = event.dispatch_attempts >= event.max_dispatch_attempts
            event.dispatch_status = DispatchStatus.FAILED if exhausted else DispatchStatus.RETRY
            event.last_error_category = error_category
            event.claimed_at = None
            event.claimed_by = None
            delay = min(300, 5 * (2 ** max(event.dispatch_attempts - 1, 0)))
            event.next_attempt_at = (
                None if exhausted else self._now() + datetime.timedelta(seconds=delay)
            )
            session.add(
                AuditLogORM(
                    event_type=AuditEventType.OUTBOX_DISPATCH_FAILED.value,
                    actor_id=event.actor_id,
                    target_id=claimed.task_id,
                    target_type="async_task",
                    correlation_id=event.correlation_id,
                    causation_id=event.id,
                    source="dispatcher",
                    outcome="FAILURE",
                    detail={
                        "event_type": event.event_type,
                        "error_category": error_category,
                        "retry_exhausted": exhausted,
                    },
                )
            )
            await session.commit()

    async def dispatch_once(self, batch_size: int = 50) -> int:
        """Claim and publish one bounded batch from both existing outboxes."""
        claimed: list[ClaimedDispatch] = []
        for kind in self._MODELS:
            async with self.session_factory() as session:
                claimed.extend(await self._claim_batch(session, kind, batch_size))

        dispatched = 0
        for item in claimed:
            try:
                celery_app.send_task(
                    item.task_name,
                    kwargs={"task_id": str(item.task_id)},
                    task_id=str(item.task_id),
                    queue=item.queue,
                )
            except Exception as exc:
                await self._record_dispatch_failure(item, type(exc).__name__)
                logger.error(
                    "Outbox publication failed",
                    extra={"task_id": str(item.task_id), "error_type": type(exc).__name__},
                )
            else:
                await self._record_dispatched(item)
                dispatched += 1
        return dispatched

    async def replay(self, outbox_kind: str, event_id: str, actor_id: uuid.UUID) -> None:
        """Make a failed, unpublished event eligible for explicit operator replay."""
        model_cls = self._MODELS.get(outbox_kind)
        if model_cls is None:
            raise ValueError("Unknown outbox kind.")
        async with self.session_factory() as session:
            event = (
                await session.execute(
                    select(model_cls).where(model_cls.id == event_id).with_for_update()
                )
            ).scalar_one_or_none()
            if event is None:
                raise ValueError("Outbox event not found.")
            if event.published_at is not None:
                return
            event.dispatch_status = DispatchStatus.PENDING
            event.dispatch_attempts = 0
            event.next_attempt_at = None
            event.claimed_at = None
            event.claimed_by = None
            event.last_error_category = None
            session.add(
                AuditLogORM(
                    event_type=AuditEventType.OUTBOX_REPLAYED.value,
                    actor_id=actor_id,
                    target_id=None,
                    target_type=f"{outbox_kind}_outbox",
                    correlation_id=event.correlation_id,
                    causation_id=event.id,
                    source="dispatcher",
                    outcome="SUCCESS",
                    detail={"event_type": event.event_type},
                )
            )
            await session.commit()

    def _build_payload(self, event: Any, task_name: str) -> AsyncTaskPayload:
        config = dict(event.payload)
        raw_entity_id = config.get("entity_id") or config.get("handoff_id")
        if raw_entity_id is not None:
            entity_id = uuid.UUID(str(raw_entity_id))
            entity_type = str(config.get("entity_type") or "handoff")
        elif isinstance(event, CaseOutboxORM):
            entity_type = "case"
            entity_id = event.case_id
        else:
            entity_type = "evidence"
            entity_id = event.evidence_id
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

    @staticmethod
    def _route_task(task_name: str) -> str:
        if ".processing." in task_name:
            return "careintel_processing"
        if ".ai." in task_name:
            return "careintel_ai"
        if ".retrieval." in task_name:
            return "careintel_retrieval"
        return "careintel_workflow"

    async def poll_forever(self, interval_seconds: float = 2.0) -> None:
        logger.info("Outbox dispatcher started")
        while True:
            try:
                await self.dispatch_once()
            except Exception as exc:
                logger.error("Outbox polling error", extra={"error_type": type(exc).__name__})
                await asyncio.sleep(min(interval_seconds * 2, 30))
            else:
                await asyncio.sleep(interval_seconds)
