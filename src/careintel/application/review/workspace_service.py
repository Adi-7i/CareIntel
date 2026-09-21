"""
Reviewer Workspace Read Model.
"""

from __future__ import annotations

import uuid
from typing import Any

from careintel.core.errors import AuthorizationError, NotFoundError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class WorkspaceService:
    """Provides a consolidated, provenance-aware read model for the reviewer."""

    def __init__(self, case_repo: CaseRepository, review_repo: ReviewRepository) -> None:
        self.case_repo = case_repo
        self.review_repo = review_repo

    async def get_reviewer_workspace(self, case_id: uuid.UUID, actor: UserContext) -> dict[str, Any]:
        """
        Builds the consolidated read model.
        Returns a dictionary representing the workspace view.
        """
        # 1. Authorize
        if not AuthorizationPolicy.evaluate(actor, Permission.REVIEW_READ):
            raise AuthorizationError("Actor not authorized to read review workspace.")

        # 2. Fetch case
        case_orm = await self.case_repo.get_by_id(case_id)
        if not case_orm:
            raise NotFoundError("Case not found.")

        # 3. Fetch queue item
        queue_item = await self.review_repo.get_queue_item(case_id)

        # 4. Fetch human content (decisions, notes, escalations)
        decisions = await self.review_repo.get_decisions_for_case(case_id)
        escalations = await self.review_repo.get_escalations_for_case(case_id)
        active_note = await self.review_repo.get_active_note_for_case(case_id)

        # Note: In a complete implementation, this would also fetch:
        # - Original Evidence (from EvidenceRepository)
        # - Derived Information (from ExtractionRepository/AI)
        # - AI Drafts + Edits (from AIDraftRepository & ReviewRepository)
        # - Referral Packages (from HandoffRepository)
        
        workspace = {
            "case": {
                "id": str(case_orm.id),
                "state": case_orm.state,
                "version": case_orm.version,
                "assigned_to": str(case_orm.assigned_to) if case_orm.assigned_to else None,
            },
            "queue_item": {
                "status": queue_item.status if queue_item else None,
                "priority_bucket": queue_item.priority_bucket if queue_item else None,
            } if queue_item else None,
            "original_evidence": [], # TBD: Fetch from EvidenceRepository
            "derived_information": {
                "ocr_results": [],
                "transcripts": [],
                "extracted_facts": [],
                "timeline_events": [],
                "missing_information": [],
                "conflicts": [],
                "clarification_questions": [],
            },
            "ai_content": {
                "drafts": [], # TBD: Fetch from AIDraftRepository
                "policy_decisions": [],
            },
            "human_content": {
                "active_note": {
                    "id": str(active_note.id),
                    "content": active_note.content,
                    "version": active_note.version,
                } if active_note else None,
                "review_decisions": [
                    {
                        "id": str(d.id),
                        "decision_type": d.decision_type,
                        "rationale": d.rationale,
                        "created_at": d.created_at.isoformat(),
                    }
                    for d in decisions
                ],
                "approved_drafts": [], # TBD: Filter from AI drafts
            },
            "escalations": [
                {
                    "id": str(e.id),
                    "status": e.status,
                    "reason": e.reason,
                }
                for e in escalations
            ],
            "referral_packages": [], # TBD: Fetch from HandoffRepository
        }

        return workspace
