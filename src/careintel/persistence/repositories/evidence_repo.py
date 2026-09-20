"""
Evidence repository.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.evidence import EvidenceORM


class EvidenceRepository:
    """Repository for EvidenceORM."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, evidence: EvidenceORM) -> EvidenceORM:
        self.session.add(evidence)
        await self.session.flush()
        return evidence

    async def get_by_id(self, evidence_id: uuid.UUID) -> EvidenceORM | None:
        stmt = select(EvidenceORM).where(EvidenceORM.id == evidence_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_case_id(self, case_id: uuid.UUID) -> Sequence[EvidenceORM]:
        stmt = (
            select(EvidenceORM)
            .where(EvidenceORM.case_id == case_id)
            .order_by(EvidenceORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_state(self, evidence_id: uuid.UUID, new_state: str) -> bool:
        stmt = update(EvidenceORM).where(EvidenceORM.id == evidence_id).values(state=new_state)
        result = await self.session.execute(stmt)
        return result.rowcount == 1  # type: ignore

    async def update_storage_key(self, evidence_id: uuid.UUID, key: str) -> bool:
        stmt = update(EvidenceORM).where(EvidenceORM.id == evidence_id).values(storage_key=key)
        result = await self.session.execute(stmt)
        return result.rowcount == 1  # type: ignore

    async def get_by_checksum(self, case_id: uuid.UUID, sha256_checksum: str) -> EvidenceORM | None:
        stmt = select(EvidenceORM).where(
            EvidenceORM.case_id == case_id,
            EvidenceORM.sha256_checksum == sha256_checksum,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
