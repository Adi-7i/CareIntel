"""
Clarification Service (Reviewer-facing).
"""

from __future__ import annotations

import datetime
import uuid
from collections.abc import Sequence

from careintel.core.errors import AuthorizationError, InvalidTransitionError, NotFoundError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.review.state_machine import ReviewStateMachine
from careintel.domain.review.states import ReviewQueueStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class ClarificationService:
    """Manages clarification requests originating from reviewers."""

    def __init__(
        self,
        review_repo: ReviewRepository,
        audit_repo: AuditRepository,
        # ClarificationRepo would be injected here in full impl
    ) -> None:
        self.review_repo = review_repo
        self.audit_repo = audit_repo

    async def request_clarification(
        self, case_id: uuid.UUID, missing_item_ids: Sequence[uuid.UUID], actor: UserContext, correlation_id: str
    ) -> None:
        """Transitions queue item to CLARIFICATION_PENDING and records the request."""
        if not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_WRITE):
            raise AuthorizationError("Actor not authorized to request clarification.")

        item = await self.review_repo.get_queue_item_for_update(case_id)
        if not item:
            raise NotFoundError("Review queue item not found.")

        if item.assigned_reviewer_id != actor.id:
            raise AuthorizationError("Only assigned reviewer can request clarification.")

        try:
            ReviewStateMachine.validate_transition(item.status, ReviewQueueStatus.CLARIFICATION_PENDING)
        except InvalidTransitionError as e:
            raise InvalidTransitionError("Clarification can only be requested while IN_REVIEW.") from e

        now = datetime.datetime.now(datetime.UTC)
        item.status = ReviewQueueStatus.CLARIFICATION_PENDING.value
        item.version += 1
        item.updated_at = now

        # In a full implementation, we'd create ClarificationQuestionORM records here
        # or link them to existing MissingInfoItemORMs (Phase 6).

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.CLARIFICATION_REQUESTED_BY_REVIEWER.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={"missing_item_ids": [str(x) for x in missing_item_ids]},
            )
        )

    async def receive_clarification_response(
        self, case_id: uuid.UUID, response_data: dict, actor: UserContext, correlation_id: str
    ) -> None:
        """Transitions queue item back to IN_REVIEW once clarification is received."""
        # This could be called by a system/patient actor
        item = await self.review_repo.get_queue_item_for_update(case_id)
        if not item:
            raise NotFoundError("Review queue item not found.")

        try:
            ReviewStateMachine.validate_transition(item.status, ReviewQueueStatus.IN_REVIEW)
        except InvalidTransitionError as e:
             raise InvalidTransitionError("Clarification can only be resolved if PENDING.") from e

        now = datetime.datetime.now(datetime.UTC)
        item.status = ReviewQueueStatus.IN_REVIEW.value
        item.version += 1
        item.updated_at = now

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.CLARIFICATION_RESPONSE_RECEIVED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )
