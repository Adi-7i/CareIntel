"""
Text content repository.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.evidence import TextContentORM


class TextContentRepository:
    """Repository for Evidence Text Content."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, text_content: TextContentORM) -> TextContentORM:
        self.session.add(text_content)
        await self.session.flush()
        return text_content

    async def get_for_evidence(self, evidence_id: uuid.UUID) -> TextContentORM | None:
        result = await self.session.execute(
            select(TextContentORM).where(TextContentORM.evidence_id == evidence_id)
        )
        return result.scalar_one_or_none()
