"""
Case repository.
"""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.case import CaseORM


class CaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, case: CaseORM) -> CaseORM:
        self.session.add(case)
        await self.session.flush()
        return case

    async def get_by_id(self, case_id: uuid.UUID) -> CaseORM | None:
        return await self.session.get(CaseORM, case_id)

    async def get_for_update(self, case_id: uuid.UUID, expected_version: int) -> CaseORM | None:
        """
        Get case with pessimistic lock (SELECT ... FOR UPDATE).
        Returns None if case not found OR version does not match.
        """
        stmt = (
            select(CaseORM)
            .where(CaseORM.id == case_id)
            .where(CaseORM.version == expected_version)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_state(self, case_id: uuid.UUID, new_state: str, new_version: int) -> bool:
        """
        Update state and version using optimistic concurrency control.
        Returns True if updated, False if version mismatch (stale write).
        """
        expected_version = new_version - 1
        stmt = (
            update(CaseORM)
            .where(CaseORM.id == case_id)
            .where(CaseORM.version == expected_version)
            .values(state=new_state, version=new_version)
        )
        result = await self.session.execute(stmt)
        return result.rowcount == 1  # type: ignore
