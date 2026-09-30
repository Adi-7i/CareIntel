"""Versioned, consent-gated referral package preparation."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.core.errors import InvalidTransitionError, NotFoundError
from careintel.domain.ai.status import DraftReviewerStatus
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.states import CaseState
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.domain.review.states import ReviewDecisionType
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM
from careintel.persistence.models.handoff import ReferralPackageORM
from careintel.persistence.repositories.ai_repo import AIRepository
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.handoff_repo import HandoffRepository
from careintel.persistence.repositories.review_repo import ReviewRepository


class ReferralPackageService:
    def __init__(
        self,
        handoff_repo: HandoffRepository,
        case_repo: CaseRepository,
        evidence_repo: EvidenceRepository,
        review_repo: ReviewRepository,
        ai_repo: AIRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
    ) -> None:
        self.handoff_repo = handoff_repo
        self.case_repo = case_repo
        self.evidence_repo = evidence_repo
        self.review_repo = review_repo
        self.ai_repo = ai_repo
        self.consent_service = consent_service
        self.audit_repo = audit_repo

    async def _authorized_case(self, case_id: uuid.UUID, actor: UserContext) -> CaseORM:
        case = await self.case_repo.get_by_id(case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        PermissionService.check(actor, Permission.REFERRAL_WRITE, facility_scope=case.facility_id)
        await self.consent_service.require_active(
            case.synthetic_subject_id, ConsentPurpose.REFERRAL.value, "1.0"
        )
        return case

    async def prepare_referral_package(
        self,
        case_id: uuid.UUID,
        evidence_ids: Sequence[uuid.UUID],
        actor: UserContext,
        correlation_id: str,
    ) -> ReferralPackageORM:
        case = await self._authorized_case(case_id, actor)
        locked_case = await self.case_repo.lock_by_id(case_id)
        if locked_case is None:
            raise NotFoundError("Case not found.")
        case = locked_case
        if case.state != CaseState.REVIEWED.value:
            raise InvalidTransitionError("Referral preparation requires completed human review.")
        if not evidence_ids:
            raise InvalidTransitionError("A referral package requires selected evidence.")
        decision = await self.review_repo.get_latest_decision(case_id)
        if (
            decision is None
            or decision.case_version != case.version
            or decision.decision_type
            not in {ReviewDecisionType.APPROVE.value, ReviewDecisionType.REFER.value}
            or decision.draft_id is None
        ):
            raise InvalidTransitionError("Current case version has no valid human approval.")
        draft = await self.ai_repo.get_draft(decision.draft_id)
        if (
            draft is None
            or draft.version != decision.draft_version
            or draft.reviewer_status != DraftReviewerStatus.APPROVED.value
        ):
            raise InvalidTransitionError("Approved draft changed after the review decision.")

        evidence_refs: list[str] = []
        for evidence_id in dict.fromkeys(evidence_ids):
            evidence = await self.evidence_repo.get_by_id(evidence_id)
            if evidence is None or evidence.case_id != case_id:
                raise NotFoundError("Evidence not found for case.")
            evidence_refs.append(str(evidence.id))

        edit = await self.review_repo.get_latest_edit_for_draft(draft.id)
        approved_content = edit.edited_content_json if edit is not None else draft.content_json
        latest = await self.handoff_repo.get_latest_package_for_update(case_id)
        version = 1 if latest is None else latest.version + 1
        package = ReferralPackageORM(
            case_id=case_id,
            version=version,
            prepared_by=actor.id,
            content_json={
                "case_id": str(case_id),
                "review_decision_id": str(decision.id),
                "approved_draft_id": str(draft.id),
                "approved_draft_version": draft.version,
                "approved_reviewer_content": approved_content,
            },
            evidence_ids=evidence_refs,
            status="DRAFT",
            correlation_id=correlation_id,
        )
        await self.handoff_repo.create_referral_package(package)
        if latest is not None:
            latest.status = "SUPERSEDED"
            latest.superseded_by = package.id
        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REFERRAL_PACKAGE_CREATED.value,
                actor_id=actor.id,
                target_id=package.id,
                target_type="referral_package",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={"version": version, "evidence_count": len(evidence_refs)},
            )
        )
        return package

    async def finalize_package(
        self, package_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> ReferralPackageORM:
        package = await self.handoff_repo.get_referral_package_for_update(package_id)
        if package is None:
            raise NotFoundError("Referral package not found.")
        await self._authorized_case(package.case_id, actor)
        if package.status == "FINALIZED":
            return package
        if package.status != "DRAFT":
            raise InvalidTransitionError("Only a DRAFT referral package can be finalized.")
        package.status = "FINALIZED"
        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REFERRAL_PACKAGE_FINALIZED.value,
                actor_id=actor.id,
                target_id=package.id,
                target_type="referral_package",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )
        return package
