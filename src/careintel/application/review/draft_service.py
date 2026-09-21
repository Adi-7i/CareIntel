"""
AI Draft Review Service.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from careintel.core.errors import AuthorizationError, NotFoundError, InvalidTransitionError
from careintel.domain.ai.status import DraftReviewerStatus
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.review import DraftEditVersionORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class DraftReviewService:
    """Service for reviewers to accept, reject, or edit AI drafts."""

    def __init__(
        self,
        review_repo: ReviewRepository,
        audit_repo: AuditRepository,
        # Note: Needs AIDraftRepository in real impl
    ) -> None:
        self.review_repo = review_repo
        self.audit_repo = audit_repo
        
    # Mocking AIDraft retrieval since we don't have the repo injected here
    # and Phase 7 created AIDraftORM.
    async def _get_draft(self, draft_id: uuid.UUID) -> Any:
        """Mock method for getting draft."""
        class MockDraft:
            id = draft_id
            reviewer_status = DraftReviewerStatus.DRAFT.value
            content_json = {"mock": "content"}
            reviewer_id = None
            reviewed_at = None
        return MockDraft()

    async def accept_draft(
        self, draft_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> None:
        if not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_WRITE):
            raise AuthorizationError("Actor not authorized to review drafts.")

        draft = await self._get_draft(draft_id)
        if not draft:
            raise NotFoundError("Draft not found.")

        if draft.reviewer_status != DraftReviewerStatus.DRAFT.value:
            raise InvalidTransitionError("Only DRAFTs can be accepted.")

        now = datetime.datetime.now(datetime.UTC)
        draft.reviewer_status = DraftReviewerStatus.APPROVED.value
        draft.reviewer_id = actor.id
        draft.reviewed_at = now

        # Record explicit accept as a draft edit version (preserves original)
        edit = DraftEditVersionORM(
            draft_id=draft_id,
            editor_id=actor.id,
            original_content_json=draft.content_json,
            edited_content_json=draft.content_json, # Unchanged
            content_origin="HUMAN_APPROVED",
            correlation_id=correlation_id,
        )
        await self.review_repo.create_draft_edit(edit)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.AI_DRAFT_ACCEPTED.value,
                actor_id=actor.id,
                target_id=draft_id,
                target_type="ai_draft",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )

    async def reject_draft(
        self, draft_id: uuid.UUID, rationale: str, actor: UserContext, correlation_id: str
    ) -> None:
        if not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_WRITE):
            raise AuthorizationError("Actor not authorized to review drafts.")

        draft = await self._get_draft(draft_id)
        if not draft:
            raise NotFoundError("Draft not found.")

        if draft.reviewer_status != DraftReviewerStatus.DRAFT.value:
            raise InvalidTransitionError("Only DRAFTs can be rejected.")

        now = datetime.datetime.now(datetime.UTC)
        draft.reviewer_status = DraftReviewerStatus.REJECTED.value
        draft.reviewer_id = actor.id
        draft.reviewed_at = now

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.AI_DRAFT_REJECTED_BY_REVIEWER.value,
                actor_id=actor.id,
                target_id=draft_id,
                target_type="ai_draft",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={"rationale": rationale},
            )
        )

    async def edit_draft(
        self, draft_id: uuid.UUID, edited_content: dict, rationale: str | None, actor: UserContext, correlation_id: str
    ) -> None:
        """Edit a draft. Does NOT overwrite original AI content_json."""
        if not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_WRITE):
            raise AuthorizationError("Actor not authorized to review drafts.")

        draft = await self._get_draft(draft_id)
        if not draft:
            raise NotFoundError("Draft not found.")

        if draft.reviewer_status != DraftReviewerStatus.DRAFT.value:
             raise InvalidTransitionError("Only DRAFTs can be edited.")

        now = datetime.datetime.now(datetime.UTC)
        draft.reviewer_status = DraftReviewerStatus.APPROVED.value
        draft.reviewer_id = actor.id
        draft.reviewed_at = now

        # Save the edited version
        edit = DraftEditVersionORM(
            draft_id=draft_id,
            editor_id=actor.id,
            original_content_json=draft.content_json, # Snapshot of AI content
            edited_content_json=edited_content,       # Human edited version
            edit_rationale=rationale,
            content_origin="HUMAN_EDITED",
            correlation_id=correlation_id,
        )
        await self.review_repo.create_draft_edit(edit)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.AI_DRAFT_EDITED.value,
                actor_id=actor.id,
                target_id=draft_id,
                target_type="ai_draft",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )
