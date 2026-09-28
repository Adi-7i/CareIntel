"""Human reviewer queue and assignment application service."""

from __future__ import annotations

import datetime
import uuid

from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.application.review.access import ReviewAccessGuard
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
from careintel.domain.case.states import CaseState
from careintel.domain.review.state_machine import ReviewStateMachine
from careintel.domain.review.states import ReviewQueueStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.review import ReviewQueueItemORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.encounter_repo import EncounterRepository
from careintel.persistence.repositories.review_repo import ReviewRepository
from careintel.persistence.repositories.user_repo import UserRepository


class ReviewService:
    def __init__(
        self,
        review_repo: ReviewRepository,
        case_repo: CaseRepository,
        encounter_repo: EncounterRepository,
        user_repo: UserRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
    ) -> None:
        self.review_repo = review_repo
        self.case_repo = case_repo
        self.encounter_repo = encounter_repo
        self.user_repo = user_repo
        self.audit_repo = audit_repo
        self.access = ReviewAccessGuard(case_repo, consent_service)

    @staticmethod
    def _now() -> datetime.datetime:
        return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    async def list_queue(
        self,
        actor: UserContext,
        status: str | None = None,
        assigned_to: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReviewQueueItemORM]:
        PermissionService.check(actor, Permission.REVIEW_READ)
        items = await self.review_repo.list_queue_items(status, None, assigned_to, limit, offset)
        visible: list[ReviewQueueItemORM] = []
        for item in items:
            case = await self.case_repo.get_by_id(item.case_id)
            if case is not None and AuthorizationPolicy.evaluate(
                actor, Permission.REVIEW_READ, facility_scope=case.facility_id
            ):
                visible.append(item)
        return visible

    async def enter_review_queue(
        self,
        case_id: uuid.UUID,
        actor: UserContext,
        correlation_id: str,
        encounter_id: uuid.UUID | None = None,
    ) -> ReviewQueueItemORM:
        case = await self.access.require_case(case_id, actor, Permission.REVIEW_WRITE)
        locked_case = await self.case_repo.lock_by_id(case_id)
        if locked_case is None:
            raise NotFoundError("Case not found.")
        case = locked_case
        existing = await self.review_repo.get_queue_item(case_id)
        if existing:
            if encounter_id is not None and existing.encounter_id != encounter_id:
                raise InvalidTransitionError("Case already has a queue item for another encounter.")
            return existing
        if case.state != CaseState.REVIEW_PENDING.value:
            raise InvalidTransitionError("Case must be REVIEW_PENDING before queue entry.")
        if (
            encounter_id is not None
            and await self.encounter_repo.get_for_case(encounter_id, case_id) is None
        ):
            raise NotFoundError("Encounter not found for case.")
        item = ReviewQueueItemORM(
            case_id=case_id,
            encounter_id=encounter_id,
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

    async def _eligible_reviewer(
        self, reviewer_id: uuid.UUID, facility_id: uuid.UUID | None
    ) -> UserContext:
        reviewer = await self.user_repo.get_user_context(reviewer_id)
        if reviewer is None or not AuthorizationPolicy.evaluate(
            reviewer, Permission.REVIEW_WRITE, facility_scope=facility_id
        ):
            raise AuthorizationError("Selected reviewer is not eligible for this case.")
        return reviewer

    async def assign_reviewer(
        self,
        case_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        expected_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> ReviewQueueItemORM:
        case = await self.access.require_case(case_id, actor, Permission.REVIEW_ASSIGN)
        await self._eligible_reviewer(reviewer_id, case.facility_id)
        item = await self.review_repo.get_queue_item_for_update(case_id, expected_version)
        if item is None:
            existing = await self.review_repo.get_queue_item(case_id)
            if existing is not None:
                raise ConcurrencyError()
            raise NotFoundError("Review queue item not found.")
        ReviewStateMachine.validate_transition(item.status, ReviewQueueStatus.ASSIGNED)
        now = self._now()
        item.status = ReviewQueueStatus.ASSIGNED.value
        item.assigned_reviewer_id = reviewer_id
        item.assigned_by = actor.id
        item.assigned_at = now
        item.version += 1
        item.updated_at = now
        case.assigned_to = reviewer_id
        await self._audit_assignment(item, actor.id, correlation_id, False)
        return item

    async def reassign_reviewer(
        self,
        case_id: uuid.UUID,
        new_reviewer_id: uuid.UUID,
        reason: str,
        expected_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> ReviewQueueItemORM:
        case = await self.access.require_case(case_id, actor, Permission.REVIEW_ASSIGN)
        await self._eligible_reviewer(new_reviewer_id, case.facility_id)
        item = await self.review_repo.get_queue_item_for_update(case_id, expected_version)
        if item is None:
            raise ConcurrencyError("Review queue item is missing or stale.")
        if item.status not in {ReviewQueueStatus.ASSIGNED.value, ReviewQueueStatus.IN_REVIEW.value}:
            raise InvalidTransitionError("Review item cannot be reassigned in its current state.")
        now = self._now()
        item.previous_reviewer_id = item.assigned_reviewer_id
        item.reassignment_reason = reason
        item.assigned_reviewer_id = new_reviewer_id
        item.assigned_by = actor.id
        item.assigned_at = now
        item.status = ReviewQueueStatus.ASSIGNED.value
        item.version += 1
        item.updated_at = now
        case.assigned_to = new_reviewer_id
        await self._audit_assignment(item, actor.id, correlation_id, True)
        return item

    async def _audit_assignment(
        self, item: ReviewQueueItemORM, actor_id: uuid.UUID, correlation_id: str, reassigned: bool
    ) -> None:
        await self.audit_repo.append(
            AuditLogORM(
                event_type=(
                    AuditEventType.REVIEWER_REASSIGNED.value
                    if reassigned
                    else AuditEventType.REVIEWER_ASSIGNED.value
                ),
                actor_id=actor_id,
                target_id=item.case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={"reviewer_id": str(item.assigned_reviewer_id)},
            )
        )

    async def start_review(
        self,
        case_id: uuid.UUID,
        expected_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> ReviewQueueItemORM:
        await self.access.require_case(case_id, actor, Permission.REVIEW_WRITE)
        item = await self.review_repo.get_queue_item_for_update(case_id, expected_version)
        if item is None:
            raise ConcurrencyError("Review queue item is missing or stale.")
        self.access.require_assigned(item, actor)
        if item.status == ReviewQueueStatus.IN_REVIEW.value:
            return item
        ReviewStateMachine.validate_transition(item.status, ReviewQueueStatus.IN_REVIEW)
        item.status = ReviewQueueStatus.IN_REVIEW.value
        item.version += 1
        item.updated_at = self._now()
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
