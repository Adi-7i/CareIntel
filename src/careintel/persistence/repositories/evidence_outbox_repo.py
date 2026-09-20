"""
Evidence outbox repository.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.evidence import EvidenceOutboxORM


class EvidenceOutboxRepository:
    """Repository for Evidence outbox events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, event: EvidenceOutboxORM) -> EvidenceOutboxORM:
        """Append an event to the outbox."""
        self.session.add(event)
        await self.session.flush()
        return event
