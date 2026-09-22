"""
Review Management application service.
"""

from __future__ import annotations

import datetime
import uuid

from careintel.core.errors import (
    AuthorizationError,
    InvalidTransitionError,
    NotFoundError,
)
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.review.state_machine import ReviewStateMachine
from careintel.domain.review.states import ReviewQueueStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.review import ReviewQueueItemORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class ReviewService:
    """Orchestrates review queue and assignment operations."""

    def __init__(
        self,
        review_repo: ReviewRepository,
        case_repo: CaseRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self.review_repo = review_repo
        self.case_repo = case_repo
        self.audit_repo = audit_repo

    async def enter_review_queue(
        self, case_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> ReviewQueueItemORM:
        """
        Creates a reviewer queue item for a case when it reaches a review state.
        Idempotent operation.
        """
        existing = await self.review_repo.get_queue_item(case_id)
        if existing:
            return existing

        case_orm = await self.case_repo.get_by_id(case_id)
        if not case_orm:
            raise NotFoundError("Case not found.")

        item = ReviewQueueItemORM(
            case_id=case_id,
            status=ReviewQueueStatus.PENDING_ASSIGNMENT.value,
        )
        await self.review_repo.create_queue_item(item)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REVIEW_QUEUE_ENTERED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )
        return item

    async def assign_reviewer(
        self, case_id: uuid.UUID, reviewer_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> ReviewQueueItemORM:
        """Assigns a reviewer to a case atomically."""
        # 1. Authorize actor
        if not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_ASSIGN):
            raise AuthorizationError("Actor not authorized to assign reviewers.")

        # 2. Lock queue item
        item = await self.review_repo.get_queue_item_for_update(case_id)
        if not item:
            raise NotFoundError("Review queue item not found.")

        # 3. Validate transition
        try:
            ReviewStateMachine.validate_transition(item.status, ReviewQueueStatus.ASSIGNED)
        except InvalidTransitionError as e:
            raise InvalidTransitionError("Case is already assigned or in an invalid state for assignment.") from e

        # 4. Fetch case to check facility scope
        case_orm = await self.case_repo.get_by_id(case_id)
        if not case_orm:
            raise NotFoundError("Case not found.")

        # Note: In a real system we would also validate that `reviewer_id` is a valid user
        # with access to `case_orm.facility_id` and has REVIEW_WRITE permission.

        now = datetime.datetime.now(datetime.UTC)
        item.status = ReviewQueueStatus.ASSIGNED.value
        item.assigned_reviewer_id = reviewer_id
        item.assigned_by = actor.id
        item.assigned_at = now
        item.version += 1
        item.updated_at = now

        # Update case assigned_to
        case_orm.assigned_to = reviewer_id

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REVIEWER_ASSIGNED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={"reviewer_id": str(reviewer_id)},
            )
        )
        return item

    async def reassign_reviewer(
        self,
        case_id: uuid.UUID,
        new_reviewer_id: uuid.UUID,
        reason: str,
        actor: UserContext,
        correlation_id: str,
    ) -> ReviewQueueItemORM:
        """Reassigns a reviewer, preserving the previous reviewer history."""
        if not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_ASSIGN):
            raise AuthorizationError("Actor not authorized to reassign reviewers.")

        item = await self.review_repo.get_queue_item_for_update(case_id)
        if not item:
            raise NotFoundError("Review queue item not found.")

        # Can only reassign if currently assigned or in review
        if item.status not in (ReviewQueueStatus.ASSIGNED.value, ReviewQueueStatus.IN_REVIEW.value):
            raise InvalidTransitionError(f"Cannot reassign case in state {item.status}")

        case_orm = await self.case_repo.get_by_id(case_id)
        if not case_orm:
            raise NotFoundError("Case not found.")

        now = datetime.datetime.now(datetime.UTC)
        item.previous_reviewer_id = item.assigned_reviewer_id
        item.reassignment_reason = reason
        item.assigned_reviewer_id = new_reviewer_id
        item.assigned_by = actor.id
        item.assigned_at = now
        item.status = ReviewQueueStatus.ASSIGNED.value # Revert to ASSIGNED so they must start review
        item.version += 1
        item.updated_at = now

        case_orm.assigned_to = new_reviewer_id

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REVIEWER_REASSIGNED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={
                    "old_reviewer_id": str(item.previous_reviewer_id) if item.previous_reviewer_id else None,
                    "new_reviewer_id": str(new_reviewer_id),
                    "reason": reason,
                },
            )
        )
        return item

    async def start_review(
        self, case_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> ReviewQueueItemORM:
        """Reviewer explicitly starts working on the case."""
        item = await self.review_repo.get_queue_item_for_update(case_id)
        if not item:
            raise NotFoundError("Review queue item not found.")

        if item.assigned_reviewer_id != actor.id:
            raise AuthorizationError("Only the assigned reviewer can start the review.")

        try:
            ReviewStateMachine.validate_transition(item.status, ReviewQueueStatus.IN_REVIEW)
        except InvalidTransitionError as e:
            # Idempotent return if already in review
            if item.status == ReviewQueueStatus.IN_REVIEW.value:
                return item
            raise e

        now = datetime.datetime.now(datetime.UTC)
        item.status = ReviewQueueStatus.IN_REVIEW.value
        item.version += 1
        item.updated_at = now

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REVIEW_STARTED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )
        return item
