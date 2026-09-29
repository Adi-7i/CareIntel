"""Human-authorized referral delivery and acknowledgement lifecycle."""

from __future__ import annotations

import datetime
import hashlib
import uuid

from ulid import ULID

from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.core.errors import (
    AuthorizationError,
    ConcurrencyError,
    InvalidTransitionError,
    NotFoundError,
)
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.state_machine import CaseStateMachine
from careintel.domain.case.states import CaseState
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.domain.handoff.state_machine import HandoffStateMachine
from careintel.domain.handoff.states import HandoffStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM, CaseOutboxORM, CaseStateHistoryORM
from careintel.persistence.models.handoff import HandoffORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_history_repo import CaseHistoryRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.handoff_repo import HandoffRepository


class HandoffService:
    def __init__(
        self,
        handoff_repo: HandoffRepository,
        case_repo: CaseRepository,
        history_repo: CaseHistoryRepository,
        outbox_repo: CaseOutboxRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
    ) -> None:
        self.handoff_repo = handoff_repo
        self.case_repo = case_repo
        self.history_repo = history_repo
        self.outbox_repo = outbox_repo
        self.consent_service = consent_service
        self.audit_repo = audit_repo

    @staticmethod
    def _now() -> datetime.datetime:
        return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    async def _authorized_case(
        self, case_id: uuid.UUID, actor: UserContext, permission: Permission
    ) -> CaseORM:
        case = await self.case_repo.get_by_id(case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        PermissionService.check(actor, permission, facility_scope=case.facility_id)
        await self.consent_service.require_active(
            case.synthetic_subject_id, ConsentPurpose.REFERRAL.value, "1.0"
        )
        return case

    @staticmethod
    def _idempotency_key(case_id: uuid.UUID, package_id: uuid.UUID, recipient_id: uuid.UUID) -> str:
        return hashlib.sha256(f"{case_id}:{package_id}:{recipient_id}".encode()).hexdigest()

    @staticmethod
    def _require_acknowledgement_recorder(
        handoff: HandoffORM,
        actor: UserContext,
        facility_id: uuid.UUID | None,
    ) -> None:
        """Limit acknowledgement/completion to the sender or recipient administrators."""
        if actor.id == handoff.sent_by:
            return
        try:
            PermissionService.check(
                actor,
                Permission.RECIPIENT_MANAGE,
                facility_scope=facility_id,
            )
        except AuthorizationError as exc:
            raise AuthorizationError(
                "Only the sender or an authorized recipient administrator may "
                "record handoff receipt."
            ) from exc

    async def initiate_handoff(
        self,
        package_id: uuid.UUID,
        recipient_id: uuid.UUID,
        actor: UserContext,
        correlation_id: str,
    ) -> HandoffORM:
        package = await self.handoff_repo.get_referral_package_for_update(package_id)
        if package is None:
            raise NotFoundError("Referral package not found.")
        case = await self._authorized_case(package.case_id, actor, Permission.HANDOFF_WRITE)
        if case.state != CaseState.REVIEWED.value:
            raise InvalidTransitionError("Handoff requires a reviewed case.")
        if package.status != "FINALIZED":
            raise InvalidTransitionError("Only a FINALIZED package can be handed off.")
        recipient = await self.handoff_repo.get_recipient(recipient_id)
        if recipient is None or not recipient.is_active:
            raise NotFoundError("Active recipient not found.")
        key = self._idempotency_key(case.id, package_id, recipient_id)
        existing = await self.handoff_repo.get_handoff_by_idempotency_key(key)
        if existing is not None:
            return existing
        handoff = HandoffORM(
            case_id=case.id,
            referral_package_id=package_id,
            recipient_id=recipient_id,
            channel=recipient.recipient_type,
            status=HandoffStatus.DRAFT.value,
            idempotency_key=key,
            sent_by=actor.id,
            correlation_id=correlation_id,
        )
        await self.handoff_repo.create_handoff(handoff)
        await self._audit(
            AuditEventType.HANDOFF_INITIATED, handoff, actor.id, correlation_id, "SUCCESS"
        )
        return handoff

    async def send_handoff(
        self,
        handoff_id: uuid.UUID,
        expected_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> HandoffORM:
        handoff = await self.handoff_repo.get_handoff_for_update(handoff_id, expected_version)
        if handoff is None:
            raise ConcurrencyError("Handoff is missing or stale.")
        case = await self._authorized_case(handoff.case_id, actor, Permission.HANDOFF_WRITE)
        if case.state != CaseState.REVIEWED.value:
            raise InvalidTransitionError("Handoff can only be sent after human review.")
        if handoff.status == HandoffStatus.READY.value:
            return handoff
        target = HandoffStatus.READY
        HandoffStateMachine.validate_transition(handoff.status, target)
        handoff.status = target.value
        handoff.version += 1
        handoff.updated_at = self._now()
        await self.outbox_repo.append(
            CaseOutboxORM(
                id=str(ULID()),
                event_type="HANDOFF_SEND_REQUESTED",
                event_version=1,
                occurred_at=self._now(),
                producer="careintel.handoff",
                correlation_id=correlation_id,
                case_id=handoff.case_id,
                actor_id=actor.id,
                aggregate_version=case.version,
                payload={
                    "handoff_id": str(handoff.id),
                    "entity_id": str(handoff.id),
                    "entity_type": "handoff",
                },
            )
        )
        await self._audit(
            AuditEventType.HANDOFF_SEND_REQUESTED,
            handoff,
            actor.id,
            correlation_id,
            "SUCCESS",
        )
        return handoff

    async def begin_delivery(self, handoff_id: uuid.UUID) -> HandoffORM:
        handoff = await self.handoff_repo.get_handoff_for_update(handoff_id)
        if handoff is None:
            raise NotFoundError("Handoff not found.")
        if handoff.status == HandoffStatus.DELIVERY_FAILED.value:
            HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.READY)
            handoff.status = HandoffStatus.READY.value
        HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.SENDING)
        handoff.status = HandoffStatus.SENDING.value
        handoff.version += 1
        handoff.updated_at = self._now()
        return handoff

    async def record_delivery_result(
        self,
        handoff_id: uuid.UUID,
        success: bool,
        reference: str | None,
        failure_reason: str | None,
        correlation_id: str,
    ) -> HandoffORM:
        handoff = await self.handoff_repo.get_handoff_for_update(handoff_id)
        if handoff is None:
            raise NotFoundError("Handoff not found.")
        if handoff.status in {
            HandoffStatus.SENT.value,
            HandoffStatus.ACKNOWLEDGED.value,
            HandoffStatus.COMPLETED.value,
        }:
            return handoff
        if handoff.status != HandoffStatus.SENDING.value:
            raise InvalidTransitionError("Handoff is not in delivery.")
        handoff.attempt_count += 1
        handoff.version += 1
        handoff.updated_at = self._now()
        if not success:
            HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.DELIVERY_FAILED)
            handoff.status = HandoffStatus.DELIVERY_FAILED.value
            handoff.failure_reason = failure_reason
            await self._audit(
                AuditEventType.HANDOFF_DELIVERY_FAILED,
                handoff,
                handoff.sent_by,
                correlation_id,
                "FAILURE",
            )
            return handoff

        HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.SENT)
        handoff.status = HandoffStatus.SENT.value
        handoff.delivery_reference = reference
        handoff.failure_reason = None
        handoff.sent_at = self._now()
        case = await self.case_repo.lock_by_id(handoff.case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        if case.state == CaseState.REVIEWED.value:
            await self._transition_case(
                case,
                CaseState.REFERRED,
                handoff.sent_by,
                correlation_id,
                "Referral delivered to configured recipient",
            )
        elif case.state != CaseState.REFERRED.value:
            raise InvalidTransitionError("Case cannot enter referral state.")
        await self._audit(
            AuditEventType.HANDOFF_SENT,
            handoff,
            handoff.sent_by,
            correlation_id,
            "SUCCESS",
        )
        return handoff

    async def record_acknowledgement(
        self,
        handoff_id: uuid.UUID,
        reference: str,
        expected_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> HandoffORM:
        handoff = await self.handoff_repo.get_handoff_for_update(handoff_id, expected_version)
        if handoff is None:
            raise ConcurrencyError("Handoff is missing or stale.")
        case = await self._authorized_case(handoff.case_id, actor, Permission.HANDOFF_WRITE)
        self._require_acknowledgement_recorder(handoff, actor, case.facility_id)
        if handoff.status == HandoffStatus.ACKNOWLEDGED.value:
            return handoff
        HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.ACKNOWLEDGED)
        handoff.status = HandoffStatus.ACKNOWLEDGED.value
        handoff.acknowledgement_reference = reference
        handoff.acknowledged_at = self._now()
        handoff.version += 1
        handoff.updated_at = self._now()
        await self._audit(
            AuditEventType.HANDOFF_ACKNOWLEDGED,
            handoff,
            actor.id,
            correlation_id,
            "SUCCESS",
        )
        return handoff

    async def complete_handoff(
        self,
        handoff_id: uuid.UUID,
        expected_handoff_version: int,
        expected_case_version: int,
        actor: UserContext,
        correlation_id: str,
    ) -> HandoffORM:
        handoff = await self.handoff_repo.get_handoff_for_update(
            handoff_id, expected_handoff_version
        )
        if handoff is None:
            raise ConcurrencyError("Handoff is missing or stale.")
        authorized_case = await self._authorized_case(
            handoff.case_id, actor, Permission.HANDOFF_WRITE
        )
        self._require_acknowledgement_recorder(handoff, actor, authorized_case.facility_id)
        if handoff.status == HandoffStatus.COMPLETED.value:
            return handoff
        HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.COMPLETED)
        case = await self.case_repo.get_for_update(handoff.case_id, expected_case_version)
        if case is None:
            raise ConcurrencyError("Case is missing or stale.")
        await self._transition_case(
            case,
            CaseState.COMPLETED,
            actor.id,
            correlation_id,
            "Recipient acknowledgement recorded",
        )
        handoff.status = HandoffStatus.COMPLETED.value
        handoff.version += 1
        handoff.updated_at = self._now()
        await self._audit(
            AuditEventType.HANDOFF_COMPLETED,
            handoff,
            actor.id,
            correlation_id,
            "SUCCESS",
        )
        return handoff

    async def _transition_case(
        self,
        case: CaseORM,
        target: CaseState,
        actor_id: uuid.UUID,
        correlation_id: str,
        reason: str,
    ) -> None:
        CaseStateMachine.validate_transition(case.state, target)
        from_state = case.state
        case.state = target.value
        case.version += 1
        now = self._now()
        await self.history_repo.append(
            CaseStateHistoryORM(
                id=uuid.uuid4(),
                case_id=case.id,
                from_state=from_state,
                to_state=case.state,
                actor_id=actor_id,
                aggregate_version=case.version,
                transitioned_at=now,
                reason=reason,
                command_type="HandoffTransition",
            )
        )
        await self.outbox_repo.append(
            CaseOutboxORM(
                id=str(ULID()),
                event_type="CASE_STATE_TRANSITION",
                event_version=1,
                occurred_at=now,
                producer="careintel.handoff",
                correlation_id=correlation_id,
                case_id=case.id,
                actor_id=actor_id,
                aggregate_version=case.version,
                payload={"from_state": from_state, "to_state": case.state, "reason": reason},
            )
        )

    async def _audit(
        self,
        event_type: AuditEventType,
        handoff: HandoffORM,
        actor_id: uuid.UUID,
        correlation_id: str,
        outcome: str,
    ) -> None:
        await self.audit_repo.append(
            AuditLogORM(
                event_type=event_type.value,
                actor_id=actor_id,
                target_id=handoff.id,
                target_type="handoff",
                correlation_id=correlation_id,
                outcome=outcome,
                detail={"status": handoff.status, "attempt_count": handoff.attempt_count},
            )
        )
