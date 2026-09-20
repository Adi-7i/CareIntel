"""
Text content repository.
"""

from __future__ import annotations

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
