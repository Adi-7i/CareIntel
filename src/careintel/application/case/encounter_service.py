"""Encounter application service."""

from __future__ import annotations

import datetime
import uuid

from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.core.errors import NotFoundError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.commands import CreateEncounterCommand
from careintel.domain.case.models import EncounterSummary
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM, EncounterORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.encounter_repo import EncounterRepository


class EncounterService:
    """Creates and reads encounters inside an authorized, consented case."""

    def __init__(
        self,
        case_repo: CaseRepository,
        encounter_repo: EncounterRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
    ) -> None:
        self._cases = case_repo
        self._encounters = encounter_repo
        self._consent = consent_service
        self._audit = audit_repo

    @staticmethod
    def _to_domain(encounter: EncounterORM) -> EncounterSummary:
        return EncounterSummary(
            encounter_id=encounter.id,
            case_id=encounter.case_id,
            encounter_type=encounter.encounter_type,
            occurred_at=encounter.occurred_at,
            notes=encounter.notes,
        )

    async def _authorized_case(
        self, case_id: uuid.UUID, actor: UserContext, write: bool
    ) -> CaseORM:
        case = await self._cases.get_by_id(case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        PermissionService.check(
            actor,
            Permission.CASE_WRITE if write else Permission.CASE_READ,
            facility_scope=case.facility_id,
        )
        return case

    async def create(self, command: CreateEncounterCommand, actor: UserContext) -> EncounterSummary:
        case = await self._authorized_case(command.case_id, actor, write=True)
        await self._consent.require_active(
            case.synthetic_subject_id,
            ConsentPurpose.DATA_PROCESSING.value,
            "1.0",
        )
        occurred_at = command.occurred_at
        if occurred_at.tzinfo is not None:
            occurred_at = occurred_at.astimezone(datetime.UTC).replace(tzinfo=None)
        encounter = await self._encounters.create(
            EncounterORM(
                id=uuid.uuid4(),
                case_id=command.case_id,
                encounter_type=command.encounter_type,
                occurred_at=occurred_at,
                notes=command.notes,
                created_by=command.actor_id,
            )
        )
        await self._audit.append(
            AuditLogORM(
                event_type=AuditEventType.ENCOUNTER_CREATED.value,
                actor_id=actor.id,
                target_id=encounter.id,
                target_type="encounter",
                correlation_id=command.correlation_id,
                outcome="SUCCESS",
                detail={"case_id": str(command.case_id)},
            )
        )
        return self._to_domain(encounter)

    async def list_for_case(
        self, case_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> list[EncounterSummary]:
        await self._authorized_case(case_id, actor, write=False)
        encounters = await self._encounters.list_for_case(case_id)
        await self._audit.append(
            AuditLogORM(
                event_type=AuditEventType.ENCOUNTER_ACCESSED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
                detail={"encounter_count": len(encounters)},
            )
        )
        return [self._to_domain(item) for item in encounters]
