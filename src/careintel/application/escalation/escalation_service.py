"""
Escalation Service.
"""

from __future__ import annotations

import datetime
import uuid

from careintel.core.errors import (
    AuthorizationError,
    ConcurrencyError,
    InvalidTransitionError,
    NotFoundError,
)
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.case.state_machine import CaseStateMachine
from careintel.domain.case.states import CaseState
from careintel.domain.review.state_machine import ReviewStateMachine
from careintel.domain.review.states import EscalationStatus, ReviewQueueStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.review import EscalationRecordORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class EscalationService:
    """Manages explicit human escalations."""

    def __init__(
        self,
        review_repo: ReviewRepository,
        case_repo: CaseRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self.review_repo = review_repo
        self.case_repo = case_repo
        self.audit_repo = audit_repo

    async def create_escalation(
        self,
        case_id: uuid.UUID,
        reason: str,
        expected_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> EscalationRecordORM:
        if not AuthorizationPolicy.evaluate(actor, Permission.ESCALATION_WRITE):
            raise AuthorizationError("Actor not authorized to escalate cases.")

        case_orm = await self.case_repo.get_for_update(case_id, expected_version)
        if not case_orm:
            raise ConcurrencyError("Case missing or modified.")

        queue_item = await self.review_repo.get_queue_item_for_update(case_id)
        if not queue_item:
            raise NotFoundError("Queue item not found.")

        # Transitions
        try:
            CaseStateMachine.validate_transition(case_orm.state, CaseState.ESCALATED)
            ReviewStateMachine.validate_transition(queue_item.status, ReviewQueueStatus.ESCALATED)
        except InvalidTransitionError as e:
            raise InvalidTransitionError("Cannot escalate case from its current state.") from e

        now = datetime.datetime.now(datetime.UTC)

        case_orm.state = CaseState.ESCALATED.value
        case_orm.version += 1

        queue_item.status = ReviewQueueStatus.ESCALATED.value
        queue_item.version += 1
        queue_item.updated_at = now

        escalation = EscalationRecordORM(
            case_id=case_id,
            escalated_by=actor.id,
            status=EscalationStatus.OPEN.value,
            reason=reason,
            correlation_id=correlation_id,
        )
        await self.review_repo.create_escalation(escalation)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.ESCALATION_CREATED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )

        # outbox_dispatcher.publish("ESCALATION_CREATED", ...) in full impl

        return escalation

    async def resolve_escalation(
        self,
        escalation_id: uuid.UUID,
        resolution_notes: str,
        expected_case_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> EscalationRecordORM:
        if not AuthorizationPolicy.evaluate(actor, Permission.ESCALATION_WRITE):
             raise AuthorizationError("Actor not authorized to resolve escalations.")

        escalation = await self.review_repo.get_escalation(escalation_id)
        if not escalation:
            raise NotFoundError("Escalation record not found.")

        if escalation.status == EscalationStatus.RESOLVED.value:
            return escalation # Idempotent

        case_id = escalation.case_id

        case_orm = await self.case_repo.get_for_update(case_id, expected_case_version)
        if not case_orm:
            raise ConcurrencyError("Case missing or modified.")

        queue_item = await self.review_repo.get_queue_item_for_update(case_id)
        if not queue_item:
            raise NotFoundError("Queue item not found.")

        # Validate transitions back
        try:
            CaseStateMachine.validate_transition(case_orm.state, CaseState.REVIEWED)
            ReviewStateMachine.validate_transition(queue_item.status, ReviewQueueStatus.IN_REVIEW)
        except InvalidTransitionError as e:
            raise InvalidTransitionError("Cannot resolve escalation from current state.") from e

        now = datetime.datetime.now(datetime.UTC)

        escalation.status = EscalationStatus.RESOLVED.value
        escalation.resolved_by = actor.id
        escalation.resolution_notes = resolution_notes
        escalation.resolved_at = now

        case_orm.state = CaseState.REVIEWED.value
        case_orm.version += 1

        queue_item.status = ReviewQueueStatus.IN_REVIEW.value
        queue_item.version += 1
        queue_item.updated_at = now

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.ESCALATION_RESOLVED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )

        return escalation
