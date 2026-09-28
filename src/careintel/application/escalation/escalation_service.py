"""Explicit, human-controlled escalation workflow."""

from __future__ import annotations

import datetime
import uuid

from ulid import ULID

from careintel.application.auth.consent_service import ConsentService
from careintel.application.review.access import ReviewAccessGuard
from careintel.core.errors import ConcurrencyError, NotFoundError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.state_machine import CaseStateMachine
from careintel.domain.case.states import CaseState
from careintel.domain.review.state_machine import ReviewStateMachine
from careintel.domain.review.states import EscalationStatus, ReviewQueueStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseOutboxORM, CaseStateHistoryORM
from careintel.persistence.models.review import EscalationRecordORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_history_repo import CaseHistoryRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class EscalationService:
    def __init__(
        self,
        review_repo: ReviewRepository,
        case_repo: CaseRepository,
        history_repo: CaseHistoryRepository,
        outbox_repo: CaseOutboxRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
    ) -> None:
        self.review_repo = review_repo
        self.case_repo = case_repo
        self.history_repo = history_repo
        self.outbox_repo = outbox_repo
        self.audit_repo = audit_repo
        self.access = ReviewAccessGuard(case_repo, consent_service)

    @staticmethod
    def _now() -> datetime.datetime:
        return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    async def create_escalation(
        self,
        case_id: uuid.UUID,
        reason: str,
        expected_case_version: int,
        expected_queue_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> EscalationRecordORM:
        await self.access.require_case(case_id, actor, Permission.ESCALATION_WRITE)
        case = await self.case_repo.lock_by_id(case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        existing = await self.review_repo.get_open_escalation(case_id)
        if existing is not None:
            return existing
        if case.version != expected_case_version:
            raise ConcurrencyError("Case is stale.")
        queue = await self.review_repo.get_queue_item_for_update(case_id, expected_queue_version)
        if case is None or queue is None:
            raise ConcurrencyError("Case or review queue is missing or stale.")
        self.access.require_assigned(queue, actor)
        CaseStateMachine.validate_transition(case.state, CaseState.ESCALATED)
        ReviewStateMachine.validate_transition(queue.status, ReviewQueueStatus.ESCALATED)
        now = self._now()
        from_state = case.state
        case.state = CaseState.ESCALATED.value
        case.version += 1
        queue.status = ReviewQueueStatus.ESCALATED.value
        queue.version += 1
        queue.updated_at = now
        escalation = EscalationRecordORM(
            case_id=case_id,
            escalated_by=actor.id,
            status=EscalationStatus.OPEN.value,
            reason=reason,
            correlation_id=correlation_id,
        )
        await self.review_repo.create_escalation(escalation)
        await self._record_transition(
            case_id,
            actor.id,
            from_state,
            case.state,
            case.version,
            correlation_id,
            "Escalation created",
            AuditEventType.ESCALATION_CREATED,
            escalation.id,
        )
        return escalation

    async def resolve_escalation(
        self,
        escalation_id: uuid.UUID,
        resolution_notes: str,
        expected_case_version: int,
        expected_queue_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> EscalationRecordORM:
        escalation = await self.review_repo.get_escalation_for_update(escalation_id)
        if escalation is None:
            raise NotFoundError("Escalation record not found.")
        await self.access.require_case(escalation.case_id, actor, Permission.ESCALATION_WRITE)
        if escalation.status == EscalationStatus.RESOLVED.value:
            return escalation
        case = await self.case_repo.get_for_update(escalation.case_id, expected_case_version)
        queue = await self.review_repo.get_queue_item_for_update(
            escalation.case_id, expected_queue_version
        )
        if case is None or queue is None:
            raise ConcurrencyError("Case or review queue is missing or stale.")
        self.access.require_assigned(queue, actor)
        CaseStateMachine.validate_transition(case.state, CaseState.REVIEW_PENDING)
        ReviewStateMachine.validate_transition(queue.status, ReviewQueueStatus.IN_REVIEW)
        now = self._now()
        from_state = case.state
        escalation.status = EscalationStatus.RESOLVED.value
        escalation.resolved_by = actor.id
        escalation.resolution_notes = resolution_notes
        escalation.resolved_at = now
        case.state = CaseState.REVIEW_PENDING.value
        case.version += 1
        queue.status = ReviewQueueStatus.IN_REVIEW.value
        queue.version += 1
        queue.updated_at = now
        await self._record_transition(
            case.id,
            actor.id,
            from_state,
            case.state,
            case.version,
            correlation_id,
            "Escalation resolved; returned to human review",
            AuditEventType.ESCALATION_RESOLVED,
            escalation.id,
        )
        return escalation

    async def _record_transition(
        self,
        case_id: uuid.UUID,
        actor_id: uuid.UUID,
        from_state: str,
        to_state: str,
        version: int,
        correlation_id: str,
        reason: str,
        audit_event: AuditEventType,
        escalation_id: uuid.UUID,
    ) -> None:
        now = self._now()
        await self.history_repo.append(
            CaseStateHistoryORM(
                id=uuid.uuid4(),
                case_id=case_id,
                from_state=from_state,
                to_state=to_state,
                actor_id=actor_id,
                aggregate_version=version,
                transitioned_at=now,
                reason=reason,
                command_type="HumanEscalation",
            )
        )
        await self.outbox_repo.append(
            CaseOutboxORM(
                id=str(ULID()),
                event_type=audit_event.name,
                event_version=1,
                occurred_at=now,
                producer="careintel.escalation",
                correlation_id=correlation_id,
                case_id=case_id,
                actor_id=actor_id,
                aggregate_version=version,
                payload={"escalation_id": str(escalation_id), "state": to_state},
            )
        )
        await self.audit_repo.append(
            AuditLogORM(
                event_type=audit_event.value,
                actor_id=actor_id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={"escalation_id": str(escalation_id)},
            )
        )
