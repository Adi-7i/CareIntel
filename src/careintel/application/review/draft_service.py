"""Human actions on immutable AI drafts."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from careintel.application.auth.consent_service import ConsentService
from careintel.application.review.access import ReviewAccessGuard
from careintel.core.errors import ConcurrencyError, InvalidTransitionError, NotFoundError
from careintel.domain.ai.status import DraftReviewerStatus
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.review.states import ReviewQueueStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.review import DraftEditVersionORM
from careintel.persistence.repositories.ai_repo import AIRepository
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class DraftReviewService:
    def __init__(
        self,
        ai_repo: AIRepository,
        review_repo: ReviewRepository,
        case_repo: CaseRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
    ) -> None:
        self.ai_repo = ai_repo
        self.review_repo = review_repo
        self.audit_repo = audit_repo
        self.access = ReviewAccessGuard(case_repo, consent_service)

    @staticmethod
    def _now() -> datetime.datetime:
        return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    async def _locked_context(
        self,
        draft_id: uuid.UUID,
        expected_draft_version: int,
        expected_queue_version: int,
        actor: UserContext,
    ) -> tuple[Any, Any, uuid.UUID]:
        case_id = await self.ai_repo.get_draft_case_id(draft_id)
        if case_id is None:
            raise NotFoundError("Draft not found.")
        await self.access.require_case(case_id, actor, Permission.REVIEW_WRITE)
        queue = await self.review_repo.get_queue_item_for_update(case_id, expected_queue_version)
        if queue is None:
            raise ConcurrencyError("Review queue item is missing or stale.")
        self.access.require_assigned(queue, actor)
        if queue.status != ReviewQueueStatus.IN_REVIEW.value:
            raise InvalidTransitionError("Draft actions require an active review.")
        draft = await self.ai_repo.get_draft_for_update(draft_id, expected_draft_version)
        if draft is None:
            raise ConcurrencyError("Draft is missing or stale.")
        if draft.reviewer_status != DraftReviewerStatus.DRAFT.value:
            raise InvalidTransitionError("Only a DRAFT can receive a review action.")
        return draft, queue, case_id

    async def accept_draft(
        self,
        draft_id: uuid.UUID,
        expected_draft_version: int,
        expected_queue_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> Any:
        draft, _queue, _case_id = await self._locked_context(
            draft_id, expected_draft_version, expected_queue_version, actor
        )
        draft.reviewer_status = DraftReviewerStatus.APPROVED.value
        draft.reviewer_id = actor.id
        draft.reviewed_at = self._now()
        draft.version += 1
        await self.review_repo.create_draft_edit(
            DraftEditVersionORM(
                draft_id=draft_id,
                editor_id=actor.id,
                original_content_json=draft.content_json,
                edited_content_json=draft.content_json,
                content_origin="HUMAN_ACCEPTED",
                correlation_id=correlation_id,
            )
        )
        await self._audit(AuditEventType.AI_DRAFT_ACCEPTED, draft_id, actor.id, correlation_id)
        return draft

    async def reject_draft(
        self,
        draft_id: uuid.UUID,
        rationale: str,
        expected_draft_version: int,
        expected_queue_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> Any:
        draft, _queue, _case_id = await self._locked_context(
            draft_id, expected_draft_version, expected_queue_version, actor
        )
        draft.reviewer_status = DraftReviewerStatus.REJECTED.value
        draft.reviewer_id = actor.id
        draft.reviewed_at = self._now()
        draft.version += 1
        await self.review_repo.create_draft_edit(
            DraftEditVersionORM(
                draft_id=draft_id,
                editor_id=actor.id,
                original_content_json=draft.content_json,
                edited_content_json=draft.content_json,
                edit_rationale=rationale,
                content_origin="HUMAN_REJECTED",
                correlation_id=correlation_id,
            )
        )
        await self._audit(
            AuditEventType.AI_DRAFT_REJECTED_BY_REVIEWER,
            draft_id,
            actor.id,
            correlation_id,
        )
        return draft

    async def edit_draft(
        self,
        draft_id: uuid.UUID,
        edited_content: dict[str, Any],
        rationale: str | None,
        expected_draft_version: int,
        expected_queue_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> Any:
        draft, _queue, _case_id = await self._locked_context(
            draft_id, expected_draft_version, expected_queue_version, actor
        )
        if not edited_content:
            raise InvalidTransitionError("Edited draft content cannot be empty.")
        await self.review_repo.create_draft_edit(
            DraftEditVersionORM(
                draft_id=draft_id,
                editor_id=actor.id,
                original_content_json=draft.content_json,
                edited_content_json=edited_content,
                edit_rationale=rationale,
                content_origin="HUMAN_EDITED",
                correlation_id=correlation_id,
            )
        )
        draft.reviewer_status = DraftReviewerStatus.APPROVED.value
        draft.reviewer_id = actor.id
        draft.reviewed_at = self._now()
        draft.version += 1
        await self._audit(AuditEventType.AI_DRAFT_EDITED, draft_id, actor.id, correlation_id)
        return draft

    async def _audit(
        self,
        event_type: AuditEventType,
        draft_id: uuid.UUID,
        actor_id: uuid.UUID,
        correlation_id: str,
    ) -> None:
        await self.audit_repo.append(
            AuditLogORM(
                event_type=event_type.value,
                actor_id=actor_id,
                target_id=draft_id,
                target_type="ai_draft",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )
