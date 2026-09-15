"""
Consent repository.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.consent import ConsentEventORM, ConsentORM


class ConsentRepository:
    """Repository for Consent records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active(
        self, subject_id: uuid.UUID, purpose: str, notice_version: str
    ) -> ConsentORM | None:
        """Get an active consent record for the exact purpose and version."""
        stmt = (
            select(ConsentORM)
            .where(ConsentORM.subject_id == subject_id)
            .where(ConsentORM.purpose == purpose)
            .where(ConsentORM.notice_version == notice_version)
            .where(ConsentORM.state == "ACTIVE")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, consent_id: uuid.UUID) -> ConsentORM | None:
        """Get consent record by ID."""
        return await self.session.get(ConsentORM, consent_id)

    async def create(
        self,
        consent: ConsentORM,
        event: ConsentEventORM,
    ) -> ConsentORM:
        """Create a new consent record and its initial event."""
        self.session.add(consent)
        self.session.add(event)
        await self.session.flush()
        return consent

    async def add_event(self, event: ConsentEventORM) -> ConsentEventORM:
        """Add an event (e.g. captured, withdrawn) to an existing consent."""
        self.session.add(event)
        await self.session.flush()
        return event
