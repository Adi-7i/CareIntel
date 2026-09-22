"""
Knowledge Service.

Use-case orchestrator for the trusted knowledge corpus.

Responsibilities:
- Create and version knowledge sources
- Chunk source content for retrieval
- Compute and store embeddings
- Manage publication status transitions
- Authorize access via RBAC
- Audit knowledge management actions

CRITICAL INVARIANTS:
- Patient data must NEVER be ingested into the knowledge corpus.
- AI-generated content must NEVER be ingested into the knowledge corpus.
- Source authority and corpus membership must remain configurable.
- Historical versions are preserved; never deleted.
"""

from __future__ import annotations

import datetime
import hashlib
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.knowledge.chunker import TextChunker
from careintel.core.config import Settings
from careintel.core.correlation import get_correlation_id
from careintel.core.errors import NotFoundError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.knowledge.models import (
    KnowledgeChunk,
    KnowledgeSource,
    KnowledgeVersion,
)
from careintel.domain.knowledge.status import ChunkStatus, PublicationStatus
from careintel.infrastructure.embedding.port import EmbeddingProvider
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.knowledge import (
    KnowledgeChunkORM,
    KnowledgeSourceORM,
    KnowledgeVersionORM,
)
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.knowledge_repo import KnowledgeRepository


class KnowledgeService:
    """
    Application service for the trusted knowledge corpus.

    This service enforces authorization on all mutations and
    audits all significant operations.
    """

    def __init__(
        self,
        session: AsyncSession,
        knowledge_repo: KnowledgeRepository,
        audit_repo: AuditRepository,
        embedding_provider: EmbeddingProvider,
        settings: Settings,
        chunker: TextChunker | None = None,
    ) -> None:
        self._session = session
        self._repo = knowledge_repo
        self._audit = audit_repo
        self._embedding = embedding_provider
        self._settings = settings
        self._chunker = chunker or TextChunker()

    async def _audit_event(
        self,
        event_type: AuditEventType,
        actor_id: uuid.UUID,
        target_id: uuid.UUID | None,
        target_type: str | None,
        outcome: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Write an audit record using the existing AuditRepository API."""
        entry = AuditLogORM(
            event_type=event_type.value,
            actor_id=actor_id,
            target_id=target_id,
            target_type=target_type,
            correlation_id=get_correlation_id(),
            outcome=outcome,
            detail=detail,
        )
        await self._audit.append(entry)

    # ── Source Creation ────────────────────────────────────────────────────────

    async def create_source(
        self,
        actor: UserContext,
        name: str,
        source_type: str,
        owner: str | None = None,
        effective_date: datetime.date | None = None,
        metadata: dict[str, str] | None = None,
    ) -> KnowledgeSourceORM:
        """
        Create a new knowledge source in DRAFT status.

        Requires: KNOWLEDGE_WRITE permission.
        """
        self._require_permission(actor, Permission.KNOWLEDGE_WRITE)

        orm = await self._repo.create_source(
            {
                "name": name,
                "source_type": source_type,
                "owner": owner,
                "publication_status": PublicationStatus.DRAFT.value,
                "effective_date": effective_date,
                "created_by": actor.id,
                "metadata_json": metadata or {},
            }
        )
        await self._session.commit()

        await self._audit_event(
            event_type=AuditEventType.KNOWLEDGE_CREATED,
            actor_id=actor.id,
            target_id=orm.id,
            target_type="knowledge_source",
            outcome="success",
            detail={"name": name, "source_type": source_type},
        )
        return orm

    # ── Version Creation + Chunking ─────────────────────────────────────────

    async def create_version(
        self,
        actor: UserContext,
        source_id: uuid.UUID,
        version_key: str,
        content: str,
        corpus_version: str,
    ) -> tuple[KnowledgeVersionORM, list[KnowledgeChunkORM]]:
        """
        Create a versioned snapshot of a source and chunk its content.

        Idempotent: if (source_id, version_key) already exists, returns
        the existing version and its chunks.

        Requires: KNOWLEDGE_WRITE permission.
        """
        self._require_permission(actor, Permission.KNOWLEDGE_WRITE)

        source = await self._repo.get_source(source_id)
        if source is None:
            raise NotFoundError(f"Knowledge source {source_id} not found.")

        # Idempotency: return existing version if already created
        existing = await self._repo.get_version_by_key(source_id, version_key)
        if existing is not None:
            chunks = await self._repo.get_chunks_for_version(existing.id)
            return existing, chunks

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        version_orm = await self._repo.create_version(
            {
                "source_id": source_id,
                "version_key": version_key,
                "content_hash": content_hash,
                "corpus_version": corpus_version,
            }
        )

        # Chunk the content
        text_chunks = self._chunker.chunk(content)
        chunk_data = [
            {
                "version_id": version_orm.id,
                "chunk_index": tc.chunk_index,
                "content": tc.content,
                "token_count": tc.token_count,
                "status": "ACTIVE",
                "metadata_json": {},
            }
            for tc in text_chunks
        ]
        chunk_orms = await self._repo.create_chunks(chunk_data) if chunk_data else []

        await self._session.commit()

        await self._audit_event(
            event_type=AuditEventType.KNOWLEDGE_VERSION_CREATED,
            actor_id=actor.id,
            target_id=version_orm.id,
            target_type="knowledge_version",
            outcome="success",
            detail={
                "source_id": str(source_id),
                "version_key": version_key,
                "chunk_count": len(chunk_orms),
                "corpus_version": corpus_version,
            },
        )
        return version_orm, chunk_orms

    # ── Embedding ─────────────────────────────────────────────────────────────

    async def embed_version_chunks(
        self,
        actor: UserContext,
        version_id: uuid.UUID,
    ) -> int:
        """
        Compute and store embeddings for all chunks of a version.

        Idempotent: skips chunks that already have an embedding for
        the current provider's version_key.

        Returns: number of embeddings created.
        """
        self._require_permission(actor, Permission.KNOWLEDGE_WRITE)

        chunks = await self._repo.get_chunks_for_version(version_id)
        if not chunks:
            return 0

        # Ensure embedding version is registered
        vkey = self._embedding.version_key
        model_name = vkey.split("-")[1] if "-" in vkey else "demo"
        embedding_version_orm = await self._repo.get_or_create_embedding_version(
            {
                "provider": "demo",
                "model": model_name,
                "dimension": self._embedding.dimension,
                "version_key": vkey,
            }
        )

        # Batch embed all chunk contents
        texts = [c.content for c in chunks]
        results = await self._embedding.embed_batch(texts)

        # Dimension safety check
        for result in results:
            if result.dimension != embedding_version_orm.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: provider returned {result.dimension}, "
                    f"expected {embedding_version_orm.dimension}. "
                    "Do not mix incompatible embedding dimensions."
                )

        created = 0
        for chunk_orm, embed_result in zip(chunks, results, strict=True):
            existing = await self._repo.get_embedding_for_chunk(
                chunk_orm.id, embedding_version_orm.id
            )
            if existing is not None:
                continue  # Idempotent: already embedded

            # Create the metadata row
            embed_orm = await self._repo.create_chunk_embedding(
                {
                    "chunk_id": chunk_orm.id,
                    "embedding_version_id": embedding_version_orm.id,
                }
            )

            # Write the actual vector via raw pgvector SQL
            vector_str = "[" + ",".join(str(v) for v in embed_result.vector) + "]"
            await self._session.execute(
                text(
                    "UPDATE chunk_embeddings SET embedding = :vec::vector "
                    "WHERE id = :eid"
                ),
                {"vec": vector_str, "eid": embed_orm.id},
            )
            created += 1

        await self._session.commit()
        return created

    # ── Publication ───────────────────────────────────────────────────────────

    async def publish_source(
        self, actor: UserContext, source_id: uuid.UUID
    ) -> None:
        """
        Transition a DRAFT source to PUBLISHED status.

        Requires: KNOWLEDGE_WRITE permission.
        """
        self._require_permission(actor, Permission.KNOWLEDGE_WRITE)

        source = await self._repo.get_source(source_id)
        if source is None:
            raise NotFoundError(f"Knowledge source {source_id} not found.")
        if source.publication_status == PublicationStatus.PUBLISHED.value:
            return  # Idempotent

        await self._repo.update_source_status(source_id, PublicationStatus.PUBLISHED.value)
        await self._session.commit()

        await self._audit_event(
            event_type=AuditEventType.KNOWLEDGE_PUBLISHED,
            actor_id=actor.id,
            target_id=source_id,
            target_type="knowledge_source",
            outcome="success",
            detail={"source_id": str(source_id)},
        )

    async def retire_source(
        self, actor: UserContext, source_id: uuid.UUID
    ) -> None:
        """
        Retire a knowledge source. Historical records are preserved.

        Requires: KNOWLEDGE_WRITE permission.
        """
        self._require_permission(actor, Permission.KNOWLEDGE_WRITE)

        source = await self._repo.get_source(source_id)
        if source is None:
            raise NotFoundError(f"Knowledge source {source_id} not found.")

        await self._repo.update_source_status(source_id, PublicationStatus.RETIRED.value)
        await self._session.commit()

        await self._audit_event(
            event_type=AuditEventType.KNOWLEDGE_RETIRED,
            actor_id=actor.id,
            target_id=source_id,
            target_type="knowledge_source",
            outcome="success",
            detail={"source_id": str(source_id)},
        )

    # ── Domain Object Mapping ─────────────────────────────────────────────────

    @staticmethod
    def _to_source_domain(orm: KnowledgeSourceORM) -> KnowledgeSource:
        return KnowledgeSource(
            source_id=orm.id,
            name=orm.name,
            source_type=orm.source_type,
            owner=orm.owner,
            publication_status=PublicationStatus(orm.publication_status),
            effective_date=orm.effective_date,
            retirement_date=orm.retirement_date,
            created_by=orm.created_by,
            created_at=orm.created_at,
            metadata=dict(orm.metadata_json),
        )

    @staticmethod
    def _to_version_domain(orm: KnowledgeVersionORM) -> KnowledgeVersion:
        return KnowledgeVersion(
            version_id=orm.id,
            source_id=orm.source_id,
            version_key=orm.version_key,
            content_hash=orm.content_hash,
            corpus_version=orm.corpus_version,
            created_at=orm.created_at,
        )

    @staticmethod
    def _to_chunk_domain(orm: KnowledgeChunkORM) -> KnowledgeChunk:
        return KnowledgeChunk(
            chunk_id=orm.id,
            version_id=orm.version_id,
            chunk_index=orm.chunk_index,
            content=orm.content,
            token_count=orm.token_count,
            status=ChunkStatus(orm.status),
            metadata=dict(orm.metadata_json),
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _require_permission(actor: UserContext, permission: Permission) -> None:
        from careintel.application.auth.permission_service import PermissionService

        PermissionService.check(actor=actor, action=permission)
