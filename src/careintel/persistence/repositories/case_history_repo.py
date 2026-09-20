"""
Case State History repository.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.case import CaseStateHistoryORM


class CaseHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, entry: CaseStateHistoryORM) -> CaseStateHistoryORM:
        """Append a new state history record."""
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_for_case(self, case_id: uuid.UUID) -> list[CaseStateHistoryORM]:
        """List state history for a case, ordered by version ascending."""
        stmt = (
            select(CaseStateHistoryORM)
            .where(CaseStateHistoryORM.case_id == case_id)
            .order_by(CaseStateHistoryORM.aggregate_version.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
