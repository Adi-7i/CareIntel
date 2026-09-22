"""
Referral Package Service.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from careintel.core.errors import AuthorizationError, ConsentError, NotFoundError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.case.states import CaseState
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.handoff import ReferralPackageORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.handoff_repo import HandoffRepository


class ReferralPackageService:
    """Manages the creation and versioning of Referral Packages."""

    def __init__(
        self,
        handoff_repo: HandoffRepository,
        case_repo: CaseRepository,
        audit_repo: AuditRepository,
        # ConsentRepo, EvidenceRepo, ReviewRepo, etc. would be injected in full impl
    ) -> None:
        self.handoff_repo = handoff_repo
        self.case_repo = case_repo
        self.audit_repo = audit_repo

    # Mocking for phase 9 structure demonstration
    async def _check_consent(self, subject_id: uuid.UUID) -> bool:
        """Mock check for REFERRAL consent."""
        return True

    async def prepare_referral_package(
        self,
        case_id: uuid.UUID,
        evidence_ids: Sequence[uuid.UUID],
        actor: UserContext,
        correlation_id: str,
    ) -> ReferralPackageORM:
        if not AuthorizationPolicy.evaluate(actor, Permission.REFERRAL_WRITE):
            raise AuthorizationError("Actor not authorized to prepare referral packages.")

        case_orm = await self.case_repo.get_by_id(case_id)
        if not case_orm:
            raise NotFoundError("Case not found.")

        # 1. Gate: Check Consent
        has_consent = await self._check_consent(case_orm.patient_id)
        if not has_consent:
             # Audit the denied attempt
             await self.audit_repo.append(
                 AuditLogORM(
                     event_type=AuditEventType.REFERRAL_CONSENT_DENIED.value,
                     actor_id=actor.id,
                     target_id=case_id,
                     target_type="case",
                     correlation_id=correlation_id,
                     outcome="FAILURE",
                 )
             )
             raise ConsentError("Active consent for REFERRAL is required.")

        # 2. Gate: Case State must allow referral
        if case_orm.state not in (CaseState.REFERRED.value, CaseState.COMPLETED.value):
             # Depending on exact workflow, they might prepare it in REVIEWED just before transition
             pass

        # 3. Data minimization: Validate provided evidence_ids exist and are linked to case
        # (Omitted in this mock, but would query EvidenceRepository)

        # 4. Handle versioning
        latest_package = await self.handoff_repo.get_latest_package_for_case(case_id)
        version = 1
        if latest_package:
            if latest_package.status == "DRAFT":
                 # Could update the draft instead of creating a new version
                 pass
            version = latest_package.version + 1
            latest_package.status = "SUPERSEDED" # If it wasn't finalized

        # 5. Compile content (Mock)
        content_json: dict[str, Any] = {
            "case_id": str(case_id),
            "patient_id": str(case_orm.patient_id),
            "evidence_refs": [str(e) for e in evidence_ids],
            "approved_facts": [], # Would pull from approved AI drafts
        }

        package = ReferralPackageORM(
            case_id=case_id,
            version=version,
            prepared_by=actor.id,
            content_json=content_json,
            evidence_ids=[str(e) for e in evidence_ids],
            status="DRAFT",
            superseded_by=None,
            correlation_id=correlation_id,
        )
        await self.handoff_repo.create_referral_package(package)

        if latest_package:
             package.superseded_by = latest_package.id

        await self.audit_repo.append(
             AuditLogORM(
                 event_type=AuditEventType.REFERRAL_PACKAGE_CREATED.value,
                 actor_id=actor.id,
                 target_id=package.id,
                 target_type="referral_package",
                 correlation_id=correlation_id,
                 outcome="SUCCESS",
                 detail={"version": version},
             )
        )
        return package

    async def finalize_package(
        self, package_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> ReferralPackageORM:
        if not AuthorizationPolicy.evaluate(actor, Permission.REFERRAL_WRITE):
            raise AuthorizationError("Actor not authorized to finalize packages.")

        package = await self.handoff_repo.get_referral_package(package_id)
        if not package:
            raise NotFoundError("Package not found.")

        if package.status != "DRAFT":
             return package # Idempotent if already FINALIZED or SUPERSEDED

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
