"""
Evidence state history repository.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.evidence import EvidenceStateHistoryORM


class EvidenceHistoryRepository:
    """Repository for Evidence state transition history."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, entry: EvidenceStateHistoryORM) -> EvidenceStateHistoryORM:
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_for_evidence(self, evidence_id: uuid.UUID) -> Sequence[EvidenceStateHistoryORM]:
        stmt = (
            select(EvidenceStateHistoryORM)
            .where(EvidenceStateHistoryORM.evidence_id == evidence_id)
            .order_by(EvidenceStateHistoryORM.transitioned_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
