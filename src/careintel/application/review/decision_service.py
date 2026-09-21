"""
Review Decision Service.
"""

from __future__ import annotations

import datetime
import uuid

from careintel.core.errors import AuthorizationError, ConcurrencyError, InvalidTransitionError, NotFoundError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.case.state_machine import CaseStateMachine
from careintel.domain.case.states import CaseState
from careintel.domain.review.state_machine import ReviewStateMachine
from careintel.domain.review.states import ReviewDecisionType, ReviewQueueStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.review import ReviewDecisionORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class ReviewDecisionService:
    """Handles the final human decision for a case under review."""

    def __init__(
        self,
        review_repo: ReviewRepository,
        case_repo: CaseRepository,
        audit_repo: AuditRepository,
        # outbox_dispatcher would be injected to write events for Phase 8 workers
    ) -> None:
        self.review_repo = review_repo
        self.case_repo = case_repo
        self.audit_repo = audit_repo

    async def submit_decision(
        self,
        case_id: uuid.UUID,
        decision_type: ReviewDecisionType,
        rationale: str | None,
        expected_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> None:
        """
        Submits a review decision.
        Uses optimistic concurrency on both CaseORM and ReviewQueueItemORM.
        """
        if not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_WRITE):
            raise AuthorizationError("Actor not authorized to submit review decisions.")

        # 1. Pessimistic lock on Case + optimistic version check
        case_orm = await self.case_repo.get_for_update(case_id, expected_version)
        if not case_orm:
            # Check if it's missing entirely or just version mismatch
            existing = await self.case_repo.get_by_id(case_id)
            if existing:
                raise ConcurrencyError("Case has been modified by another request.")
            raise NotFoundError("Case not found.")

        # 2. Lock Queue Item
        queue_item = await self.review_repo.get_queue_item_for_update(case_id)
        if not queue_item:
            raise NotFoundError("Review queue item not found.")

        # 3. Validate actor is assigned reviewer (or has override permission)
        if queue_item.assigned_reviewer_id != actor.id and not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_ASSIGN):
            raise AuthorizationError("Only the assigned reviewer can submit a decision.")

        # 4. Validate Queue transition
        # Typically requires being IN_REVIEW to complete
        try:
            ReviewStateMachine.validate_transition(queue_item.status, ReviewQueueStatus.REVIEW_COMPLETE)
        except InvalidTransitionError as e:
            raise InvalidTransitionError("Cannot submit decision for a case not in review.") from e

        # 5. Map decision to target CaseState
        target_case_state = CaseState.COMPLETED
        if decision_type == ReviewDecisionType.REFER:
            target_case_state = CaseState.REFERRED
        elif decision_type == ReviewDecisionType.ESCALATE:
            # We defer escalation logic to the EscalationService. This would be a 422 here if used directly.
            raise InvalidTransitionError("Use Escalation API to escalate a case.")
        
        # 6. Validate Case transition
        try:
            CaseStateMachine.validate_transition(case_orm.state, target_case_state)
        except InvalidTransitionError as e:
             raise InvalidTransitionError(f"Cannot transition case from {case_orm.state} to {target_case_state}.") from e

        now = datetime.datetime.now(datetime.UTC)

        # 7. Apply updates
        case_orm.state = target_case_state.value
        case_orm.version += 1
        
        queue_item.status = ReviewQueueStatus.REVIEW_COMPLETE.value
        queue_item.version += 1
        queue_item.updated_at = now

        decision = ReviewDecisionORM(
            case_id=case_id,
            reviewer_id=actor.id,
            decision_type=decision_type.value,
            rationale=rationale,
            case_version=case_orm.version,
            correlation_id=correlation_id,
        )
        await self.review_repo.create_decision(decision)

        # 8. Audit
        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REVIEW_DECISION_SUBMITTED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={"decision_type": decision_type.value},
            )
        )
        
        # In full impl, outbox_dispatcher.publish("REVIEW_COMPLETED", payload={...})
