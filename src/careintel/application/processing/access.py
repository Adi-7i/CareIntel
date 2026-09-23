"""Shared authorization and consent guard for processing pipelines."""

from __future__ import annotations

import uuid

from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.core.errors import NotFoundError, ValidationError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.domain.evidence.states import EvidenceState
from careintel.persistence.models.evidence import EvidenceORM
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository


class ProcessingAccessGuard:
    """Resolves evidence through its case and enforces facility and consent scope."""

    def __init__(
        self,
        evidence_repo: EvidenceRepository,
        case_repo: CaseRepository,
        consent_service: ConsentService,
    ) -> None:
        self._evidence = evidence_repo
        self._cases = case_repo
        self._consent = consent_service

    async def require_evidence(
        self,
        evidence_id: uuid.UUID,
        actor: UserContext,
        permission: Permission,
        *,
        require_ready: bool,
    ) -> EvidenceORM:
        evidence = await self._evidence.get_by_id(evidence_id)
        if evidence is None:
            raise NotFoundError("Evidence not found.")
        case = await self._cases.get_by_id(evidence.case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        PermissionService.check(
            actor,
            permission,
            facility_scope=case.facility_id,
        )
        await self._consent.require_active(
            case.synthetic_subject_id,
            ConsentPurpose.DATA_PROCESSING.value,
            "1.0",
        )
        if require_ready and evidence.state != EvidenceState.READY.value:
            raise ValidationError(
                f"Evidence must be READY for processing; current state is {evidence.state}."
            )
        return evidence

    async def require_ready_evidence(
        self, evidence_id: uuid.UUID, actor: UserContext
    ) -> EvidenceORM:
        return await self.require_evidence(
            evidence_id,
            actor,
            Permission.PROCESSING_WRITE,
            require_ready=True,
        )

    async def require_readable_evidence(
        self, evidence_id: uuid.UUID, actor: UserContext
    ) -> EvidenceORM:
        return await self.require_evidence(
            evidence_id,
            actor,
            Permission.PROCESSING_READ,
            require_ready=False,
        )
