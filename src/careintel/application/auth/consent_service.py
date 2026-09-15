"""
Consent application service.
"""

from __future__ import annotations

import uuid

from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.consent.models import ConsentContext
from careintel.domain.consent.policy import ConsentPolicy
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.consent import ConsentEventORM, ConsentORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.consent_repo import ConsentRepository


class ConsentService:
    """Service for managing user consent."""

    def __init__(
        self,
        consent_repo: ConsentRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self.consent_repo = consent_repo
        self.audit_repo = audit_repo

    async def get_active(
        self, subject_id: uuid.UUID, purpose: str, notice_version: str
    ) -> ConsentContext | None:
        """Get an active consent context if it exists."""
        orm = await self.consent_repo.get_active(subject_id, purpose, notice_version)
        if not orm:
            return None
        return ConsentContext(
            id=orm.id,
            subject_id=orm.subject_id,
            purpose=orm.purpose,
            notice_version=orm.notice_version,
            state=orm.state,
        )

    async def require_active(
        self,
        subject_id: uuid.UUID,
        purpose: str,
        notice_version: str,
    ) -> ConsentContext:
        """Require that active consent exists (throws ConsentError)."""
        ctx = await self.get_active(subject_id, purpose, notice_version)
        return ConsentPolicy.require_active(ctx, subject_id, purpose, notice_version)

    async def request_consent(
        self,
        subject_id: uuid.UUID,
        purpose: str,
        notice_version: str,
        correlation_id: str,
    ) -> ConsentContext:
        """Record a request for consent (e.g. presented to the user)."""
        consent = ConsentORM(
            subject_id=subject_id,
            purpose=purpose,
            notice_version=notice_version,
            state="REQUESTED",
        )
        event = ConsentEventORM(
            consent_id=consent.id,
            event_type="REQUESTED",
            actor_id=None,  # system request
        )
        await self.consent_repo.create(consent, event)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.CONSENT_REQUESTED,
                target_id=consent.id,
                target_type="consent",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )
        return ConsentContext(
            id=consent.id,
            subject_id=consent.subject_id,
            purpose=consent.purpose,
            notice_version=consent.notice_version,
            state=consent.state,
        )

    async def capture_consent(
        self,
        consent_id: uuid.UUID,
        actor: UserContext,
        correlation_id: str,
    ) -> ConsentContext:
        """Record that consent was granted."""
        consent = await self.consent_repo.get_by_id(consent_id)
        if not consent:
            raise ValueError("Consent request not found.")

        consent.state = "ACTIVE"
        consent.captured_by = actor.id

        # we need to flush to get the current timestamp... let's just let SQLAlchemy handle it
        event = ConsentEventORM(
            consent_id=consent.id,
            event_type="CAPTURED",
            actor_id=actor.id,
        )
        await self.consent_repo.add_event(event)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.CONSENT_CAPTURED,
                actor_id=actor.id,
                target_id=consent.id,
                target_type="consent",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )

        return ConsentContext(
            id=consent.id,
            subject_id=consent.subject_id,
            purpose=consent.purpose,
            notice_version=consent.notice_version,
            state=consent.state,
        )

    async def withdraw_consent(
        self,
        consent_id: uuid.UUID,
        actor: UserContext,
        correlation_id: str,
    ) -> ConsentContext:
        """Record that consent was withdrawn."""
        consent = await self.consent_repo.get_by_id(consent_id)
        if not consent:
            raise ValueError("Consent request not found.")

        consent.state = "WITHDRAWN"

        event = ConsentEventORM(
            consent_id=consent.id,
            event_type="WITHDRAWN",
            actor_id=actor.id,
        )
        await self.consent_repo.add_event(event)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.CONSENT_WITHDRAWN,
                actor_id=actor.id,
                target_id=consent.id,
                target_type="consent",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )

        return ConsentContext(
            id=consent.id,
            subject_id=consent.subject_id,
            purpose=consent.purpose,
            notice_version=consent.notice_version,
            state=consent.state,
        )
