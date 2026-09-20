"""
Case Outbox repository.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.case import CaseOutboxORM


class CaseOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, event: CaseOutboxORM) -> CaseOutboxORM:
        """Append an event to the outbox to be published asynchronously."""
        self.session.add(event)
        await self.session.flush()
        return event
