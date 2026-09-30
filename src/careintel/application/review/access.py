"""Shared authorization, consent, and assignment checks for human review."""

from __future__ import annotations

import uuid

from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.core.errors import AuthorizationError, NotFoundError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.persistence.models.case import CaseORM
from careintel.persistence.models.review import ReviewQueueItemORM
from careintel.persistence.repositories.case_repo import CaseRepository


class ReviewAccessGuard:
    def __init__(self, case_repo: CaseRepository, consent_service: ConsentService) -> None:
        self._cases = case_repo
        self._consent = consent_service

    async def require_case(
        self, case_id: uuid.UUID, actor: UserContext, permission: Permission
    ) -> CaseORM:
        case = await self._cases.get_by_id(case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        PermissionService.check(actor, permission, facility_scope=case.facility_id)
        await self._consent.require_active(
            case.synthetic_subject_id,
            ConsentPurpose.AI_ANALYSIS.value,
            "1.0",
        )
        return case

    @staticmethod
    def require_assigned(queue: ReviewQueueItemORM, actor: UserContext) -> None:
        if queue.assigned_reviewer_id == actor.id:
            return
        try:
            PermissionService.check(actor, Permission.REVIEW_ASSIGN)
        except AuthorizationError as exc:
            raise AuthorizationError("Only the assigned reviewer can access this review.") from exc
