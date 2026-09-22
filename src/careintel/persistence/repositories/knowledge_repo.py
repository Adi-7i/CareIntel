"""
Knowledge Repository.

Handles persistence for knowledge sources, versions, chunks,
embedding versions, and chunk embeddings.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.knowledge import (
    ChunkEmbeddingORM,
    EmbeddingVersionORM,
    KnowledgeChunkORM,
    KnowledgeSourceORM,
    KnowledgeVersionORM,
)


class KnowledgeRepository:
    """Data access layer for the trusted knowledge corpus."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Knowledge Sources ─────────────────────────────────────────────────────

    async def create_source(self, data: dict[str, Any]) -> KnowledgeSourceORM:
        source = KnowledgeSourceORM(**data)
        self._session.add(source)
        await self._session.flush()
        return source

    async def get_source(self, source_id: uuid.UUID) -> KnowledgeSourceORM | None:
        result = await self._session.execute(
            select(KnowledgeSourceORM).where(KnowledgeSourceORM.id == source_id)
        )
        return result.scalar_one_or_none()

    async def update_source_status(
        self, source_id: uuid.UUID, status: str
    ) -> None:
        await self._session.execute(
            update(KnowledgeSourceORM)
            .where(KnowledgeSourceORM.id == source_id)
            .values(publication_status=status)
        )

    # ── Knowledge Versions ────────────────────────────────────────────────────

    async def create_version(self, data: dict[str, Any]) -> KnowledgeVersionORM:
        version = KnowledgeVersionORM(**data)
        self._session.add(version)
        await self._session.flush()
        return version

    async def get_version(self, version_id: uuid.UUID) -> KnowledgeVersionORM | None:
        result = await self._session.execute(
            select(KnowledgeVersionORM).where(KnowledgeVersionORM.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_version_by_key(
        self, source_id: uuid.UUID, version_key: str
    ) -> KnowledgeVersionORM | None:
        result = await self._session.execute(
            select(KnowledgeVersionORM).where(
                KnowledgeVersionORM.source_id == source_id,
                KnowledgeVersionORM.version_key == version_key,
            )
        )
        return result.scalar_one_or_none()

    # ── Knowledge Chunks ──────────────────────────────────────────────────────

    async def create_chunks(
        self, chunks: list[dict[str, Any]]
    ) -> list[KnowledgeChunkORM]:
        orm_chunks = [KnowledgeChunkORM(**c) for c in chunks]
        self._session.add_all(orm_chunks)
        await self._session.flush()
        return orm_chunks

    async def get_chunks_for_version(
        self, version_id: uuid.UUID
    ) -> list[KnowledgeChunkORM]:
        result = await self._session.execute(
            select(KnowledgeChunkORM)
            .where(KnowledgeChunkORM.version_id == version_id)
            .order_by(KnowledgeChunkORM.chunk_index)
        )
        return list(result.scalars().all())

    async def get_chunk(self, chunk_id: uuid.UUID) -> KnowledgeChunkORM | None:
        result = await self._session.execute(
            select(KnowledgeChunkORM).where(KnowledgeChunkORM.id == chunk_id)
        )
        return result.scalar_one_or_none()

    # ── Embedding Versions ────────────────────────────────────────────────────

    async def get_or_create_embedding_version(
        self, data: dict[str, Any]
    ) -> EmbeddingVersionORM:
        """Idempotent: returns existing version if version_key already exists."""
        existing = await self._session.execute(
            select(EmbeddingVersionORM).where(
                EmbeddingVersionORM.version_key == data["version_key"]
            )
        )
        orm = existing.scalar_one_or_none()
        if orm is not None:
            return orm
        orm = EmbeddingVersionORM(**data)
        self._session.add(orm)
        await self._session.flush()
        return orm

    async def get_embedding_version_by_key(
        self, version_key: str
    ) -> EmbeddingVersionORM | None:
        result = await self._session.execute(
            select(EmbeddingVersionORM).where(
                EmbeddingVersionORM.version_key == version_key
            )
        )
        return result.scalar_one_or_none()

    # ── Chunk Embeddings ──────────────────────────────────────────────────────

    async def create_chunk_embedding(
        self, data: dict[str, Any]
    ) -> ChunkEmbeddingORM:
        """
        Persist a chunk embedding record.

        The actual vector is written via raw SQL using pgvector's type
        in the application service layer. This method persists the metadata row.
        """
        orm = ChunkEmbeddingORM(**data)
        self._session.add(orm)
        await self._session.flush()
        return orm

    async def get_embedding_for_chunk(
        self, chunk_id: uuid.UUID, embedding_version_id: uuid.UUID
    ) -> ChunkEmbeddingORM | None:
        result = await self._session.execute(
            select(ChunkEmbeddingORM).where(
                ChunkEmbeddingORM.chunk_id == chunk_id,
                ChunkEmbeddingORM.embedding_version_id == embedding_version_id,
            )
        )
        return result.scalar_one_or_none()
