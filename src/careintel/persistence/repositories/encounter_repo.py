"""Encounter persistence operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.case import EncounterORM


class EncounterRepository:
    """Data access for encounters, always scoped through their owning case."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, encounter: EncounterORM) -> EncounterORM:
        self.session.add(encounter)
        await self.session.flush()
        return encounter

    async def get_by_id(self, encounter_id: uuid.UUID) -> EncounterORM | None:
        return await self.session.get(EncounterORM, encounter_id)

    async def get_for_case(
        self, encounter_id: uuid.UUID, case_id: uuid.UUID
    ) -> EncounterORM | None:
        result = await self.session.execute(
            select(EncounterORM).where(
                EncounterORM.id == encounter_id,
                EncounterORM.case_id == case_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_case(self, case_id: uuid.UUID) -> list[EncounterORM]:
        result = await self.session.execute(
            select(EncounterORM)
            .where(EncounterORM.case_id == case_id)
            .order_by(EncounterORM.occurred_at, EncounterORM.created_at)
        )
        return list(result.scalars().all())
