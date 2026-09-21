"""
Handoff Service.
"""

from __future__ import annotations

import datetime
import hashlib
import uuid

from careintel.core.errors import AuthorizationError, ConsentError, InvalidTransitionError, NotFoundError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.handoff.state_machine import HandoffStateMachine
from careintel.domain.handoff.states import HandoffStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.handoff import HandoffORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.handoff_repo import HandoffRepository


class HandoffService:
    """Manages the lifecycle of a handoff delivery."""

    def __init__(
        self,
        handoff_repo: HandoffRepository,
        case_repo: CaseRepository,
        audit_repo: AuditRepository,
        # outbox_dispatcher would be injected here
    ) -> None:
        self.handoff_repo = handoff_repo
        self.case_repo = case_repo
        self.audit_repo = audit_repo

    async def _check_consent(self, subject_id: uuid.UUID) -> bool:
        """Mock check for REFERRAL consent."""
        return True

    def _generate_idempotency_key(self, case_id: uuid.UUID, package_id: uuid.UUID, recipient_id: uuid.UUID) -> str:
        s = f"{case_id}:{package_id}:{recipient_id}"
        return hashlib.sha256(s.encode()).hexdigest()

    async def initiate_handoff(
        self,
        package_id: uuid.UUID,
        recipient_id: uuid.UUID,
        actor: UserContext,
        correlation_id: str,
    ) -> HandoffORM:
        if not AuthorizationPolicy.evaluate(actor, Permission.HANDOFF_WRITE):
            raise AuthorizationError("Actor not authorized to initiate handoff.")

        package = await self.handoff_repo.get_referral_package(package_id)
        if not package:
            raise NotFoundError("Referral package not found.")

        if package.status != "FINALIZED":
             raise InvalidTransitionError("Only FINALIZED packages can be handed off.")

        case_orm = await self.case_repo.get_by_id(package.case_id)
        if not case_orm:
            raise NotFoundError("Case not found.")

        if not await self._check_consent(case_orm.patient_id):
             raise ConsentError("Active consent for REFERRAL is required.")

        recipient = await self.handoff_repo.get_recipient(recipient_id)
        if not recipient or not recipient.is_active:
             raise NotFoundError("Active recipient not found.")

        idempotency_key = self._generate_idempotency_key(case_orm.id, package_id, recipient_id)
        
        # In a real impl, we might catch a unique constraint violation on idempotency_key
        # and return the existing HandoffORM.

        handoff = HandoffORM(
            case_id=case_orm.id,
            referral_package_id=package_id,
            recipient_id=recipient_id,
            status=HandoffStatus.DRAFT.value,
            idempotency_key=idempotency_key,
            sent_by=actor.id,
            correlation_id=correlation_id,
        )
        await self.handoff_repo.create_handoff(handoff)

        await self.audit_repo.append(
             AuditLogORM(
                 event_type=AuditEventType.HANDOFF_INITIATED.value,
                 actor_id=actor.id,
                 target_id=handoff.id,
                 target_type="handoff",
                 correlation_id=correlation_id,
                 outcome="SUCCESS",
             )
        )
        return handoff

    async def send_handoff(
        self, handoff_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> HandoffORM:
        if not AuthorizationPolicy.evaluate(actor, Permission.HANDOFF_WRITE):
            raise AuthorizationError("Actor not authorized to send handoff.")

        handoff = await self.handoff_repo.get_handoff_for_update(handoff_id)
        if not handoff:
            raise NotFoundError("Handoff not found.")

        # Re-verify consent at send time
        case_orm = await self.case_repo.get_by_id(handoff.case_id)
        if not case_orm or not await self._check_consent(case_orm.patient_id):
             raise ConsentError("Consent missing or revoked. Cannot send.")

        try:
             HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.READY)
        except InvalidTransitionError as e:
             raise InvalidTransitionError("Handoff cannot be sent from current state.") from e

        # Transition through READY to SENDING
        HandoffStateMachine.validate_transition(HandoffStatus.READY, HandoffStatus.SENDING)

        now = datetime.datetime.now(datetime.UTC)
        handoff.status = HandoffStatus.SENDING.value
        handoff.sent_at = now
        handoff.version += 1
        handoff.updated_at = now

        # In full impl: outbox_dispatcher.publish("HANDOFF_SEND_REQUESTED", payload={"handoff_id": ...})

        return handoff

    async def record_delivery_result(
        self, handoff_id: uuid.UUID, success: bool, reference: str | None, failure_reason: str | None, correlation_id: str
    ) -> None:
        """Called by background worker."""
        handoff = await self.handoff_repo.get_handoff_for_update(handoff_id)
        if not handoff:
            return

        # Might already be updated if worker retried
        if handoff.status != HandoffStatus.SENDING.value:
             return

        now = datetime.datetime.now(datetime.UTC)
        handoff.attempt_count += 1
        
        if success:
             HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.SENT)
             handoff.status = HandoffStatus.SENT.value
             handoff.delivery_reference = reference
             handoff.version += 1
             handoff.updated_at = now
             
             await self.audit_repo.append(
                 AuditLogORM(
                     event_type=AuditEventType.HANDOFF_SENT.value,
                     target_id=handoff.id,
                     target_type="handoff",
                     correlation_id=correlation_id,
                     outcome="SUCCESS",
                 )
             )
        else:
             HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.DELIVERY_FAILED)
             handoff.status = HandoffStatus.DELIVERY_FAILED.value
             handoff.failure_reason = failure_reason
             handoff.version += 1
             handoff.updated_at = now
             
             await self.audit_repo.append(
                 AuditLogORM(
                     event_type=AuditEventType.HANDOFF_DELIVERY_FAILED.value,
                     target_id=handoff.id,
                     target_type="handoff",
                     correlation_id=correlation_id,
                     outcome="FAILURE",
                 )
             )

    async def record_acknowledgement(
        self, handoff_id: uuid.UUID, reference: str, actor: UserContext, correlation_id: str
    ) -> HandoffORM:
        """Manually or via webhook record acknowledgement."""
        # For simplicity, treating as actor action here. Webhook would use a system actor.
        
        handoff = await self.handoff_repo.get_handoff_for_update(handoff_id)
        if not handoff:
            raise NotFoundError("Handoff not found.")
            
        try:
             HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.ACKNOWLEDGED)
        except InvalidTransitionError:
             if handoff.status == HandoffStatus.ACKNOWLEDGED.value:
                  return handoff
             raise

        now = datetime.datetime.now(datetime.UTC)
        handoff.status = HandoffStatus.ACKNOWLEDGED.value
        handoff.acknowledgement_reference = reference
        handoff.acknowledged_at = now
        handoff.version += 1
        handoff.updated_at = now

        await self.audit_repo.append(
             AuditLogORM(
                 event_type=AuditEventType.HANDOFF_ACKNOWLEDGED.value,
                 actor_id=actor.id,
                 target_id=handoff.id,
                 target_type="handoff",
                 correlation_id=correlation_id,
                 outcome="SUCCESS",
             )
        )
        return handoff

    async def complete_handoff(
        self, handoff_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> HandoffORM:
        """Transitions ACKNOWLEDGED to COMPLETED."""
        if not AuthorizationPolicy.evaluate(actor, Permission.HANDOFF_WRITE):
            raise AuthorizationError("Actor not authorized to complete handoff.")

        handoff = await self.handoff_repo.get_handoff_for_update(handoff_id)
        if not handoff:
            raise NotFoundError("Handoff not found.")
            
        try:
             HandoffStateMachine.validate_transition(handoff.status, HandoffStatus.COMPLETED)
        except InvalidTransitionError:
             if handoff.status == HandoffStatus.COMPLETED.value:
                  return handoff
             raise

        now = datetime.datetime.now(datetime.UTC)
        handoff.status = HandoffStatus.COMPLETED.value
        handoff.version += 1
        handoff.updated_at = now

        await self.audit_repo.append(
             AuditLogORM(
                 event_type=AuditEventType.HANDOFF_COMPLETED.value,
                 actor_id=actor.id,
                 target_id=handoff.id,
                 target_type="handoff",
                 correlation_id=correlation_id,
                 outcome="SUCCESS",
             )
        )
        return handoff
