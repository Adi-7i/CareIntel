"""Explicit human approval/rejection boundary."""

from __future__ import annotations

import datetime
import uuid

from ulid import ULID

from careintel.application.auth.consent_service import ConsentService
from careintel.application.review.access import ReviewAccessGuard
from careintel.core.errors import ConcurrencyError, InvalidTransitionError, NotFoundError
from careintel.domain.ai.status import DraftReviewerStatus
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.state_machine import CaseStateMachine
from careintel.domain.case.states import CaseState
from careintel.domain.review.state_machine import ReviewStateMachine
from careintel.domain.review.states import ReviewDecisionType, ReviewQueueStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseOutboxORM, CaseStateHistoryORM
from careintel.persistence.models.review import ReviewDecisionORM
from careintel.persistence.repositories.ai_repo import AIRepository
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_history_repo import CaseHistoryRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class ReviewDecisionService:
    def __init__(
        self,
        review_repo: ReviewRepository,
        case_repo: CaseRepository,
        ai_repo: AIRepository,
        history_repo: CaseHistoryRepository,
        outbox_repo: CaseOutboxRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
    ) -> None:
        self.review_repo = review_repo
        self.case_repo = case_repo
        self.ai_repo = ai_repo
        self.history_repo = history_repo
        self.outbox_repo = outbox_repo
        self.audit_repo = audit_repo
        self.access = ReviewAccessGuard(case_repo, consent_service)

    async def submit_decision(
        self,
        case_id: uuid.UUID,
        draft_id: uuid.UUID,
        decision_type: ReviewDecisionType,
        rationale: str | None,
        expected_case_version: int,
        expected_queue_version: int,
        expected_draft_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> ReviewDecisionORM:
        await self.access.require_case(case_id, actor, Permission.REVIEW_WRITE)
        case = await self.case_repo.get_for_update(case_id, expected_case_version)
        if case is None:
            raise ConcurrencyError("Case is missing or stale.")
        queue = await self.review_repo.get_queue_item_for_update(case_id, expected_queue_version)
        if queue is None:
            raise ConcurrencyError("Review queue item is missing or stale.")
        self.access.require_assigned(queue, actor)
        draft = await self.ai_repo.get_draft_for_update(draft_id, expected_draft_version)
        if draft is None or await self.ai_repo.get_draft_case_id(draft_id) != case_id:
            raise NotFoundError("Draft not found for case.")

        if decision_type in {ReviewDecisionType.APPROVE, ReviewDecisionType.REFER}:
            if draft.reviewer_status != DraftReviewerStatus.APPROVED.value:
                raise InvalidTransitionError("Final approval requires an accepted human draft.")
        elif decision_type == ReviewDecisionType.REJECT:
            if draft.reviewer_status != DraftReviewerStatus.REJECTED.value:
                raise InvalidTransitionError("A rejection decision requires a rejected draft.")
            if not rationale:
                raise InvalidTransitionError("A rejection rationale is required.")
        else:
            raise InvalidTransitionError("Use the dedicated clarification or escalation action.")

        ReviewStateMachine.validate_transition(queue.status, ReviewQueueStatus.REVIEW_COMPLETE)
        CaseStateMachine.validate_transition(case.state, CaseState.REVIEWED)
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        from_state = case.state
        case.state = CaseState.REVIEWED.value
        case.version += 1
        queue.status = ReviewQueueStatus.REVIEW_COMPLETE.value
        queue.version += 1
        queue.updated_at = now

        decision = ReviewDecisionORM(
            case_id=case_id,
            reviewer_id=actor.id,
            draft_id=draft.id,
            draft_version=draft.version,
            decision_type=decision_type.value,
            rationale=rationale,
            case_version=case.version,
            correlation_id=correlation_id,
        )
        await self.review_repo.create_decision(decision)
        await self.history_repo.append(
            CaseStateHistoryORM(
                id=uuid.uuid4(),
                case_id=case_id,
                from_state=from_state,
                to_state=case.state,
                actor_id=actor.id,
                aggregate_version=case.version,
                transitioned_at=now,
                reason=f"Human review decision: {decision_type.value}",
                command_type="SubmitReviewDecision",
            )
        )
        await self.outbox_repo.append(
            CaseOutboxORM(
                id=str(ULID()),
                event_type="REVIEW_COMPLETED",
                event_version=1,
                occurred_at=now,
                producer="careintel.review",
                correlation_id=correlation_id,
                case_id=case_id,
                actor_id=actor.id,
                aggregate_version=case.version,
                payload={
                    "decision_id": str(decision.id),
                    "draft_id": str(draft.id),
                    "decision_type": decision_type.value,
                },
            )
        )
        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REVIEW_DECISION_SUBMITTED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={
                    "decision_type": decision_type.value,
                    "draft_id": str(draft.id),
                    "draft_version": draft.version,
                },
            )
        )
        return decision
