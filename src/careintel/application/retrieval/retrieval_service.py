"""
Retrieval Service.

Use-case orchestrator for knowledge and patient evidence retrieval.

Responsibilities:
- Hash queries for idempotency.
- Coordinate embedding provider for query vectors.
- Orchestrate Dense, Sparse, or Hybrid search.
- Fuse results using RRFFusion.
- Rerank results via RerankProvider.
- Persist retrieval run and candidate audits.
- Emit RETRIEVAL_EXECUTED audit event.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.retrieval.dense_search import DenseSearcher
from careintel.application.retrieval.fusion import RRFFusion
from careintel.application.retrieval.sparse_search import SparseSearcher
from careintel.core.config import Settings
from careintel.core.correlation import get_correlation_id
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.retrieval.models import (
    RetrievalCandidate,
    RetrievalMetadata,
    RetrievalResult,
)
from careintel.domain.retrieval.status import RetrievalStatus, SearchMode
from careintel.infrastructure.embedding.port import EmbeddingProvider
from careintel.infrastructure.reranker.port import RerankProvider
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.retrieval import RetrievalCandidateORM, RetrievalRunORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.retrieval_repo import RetrievalRepository


class RetrievalService:
    """Orchestrates hybrid search, fusion, and reranking."""

    def __init__(
        self,
        session: AsyncSession,
        retrieval_repo: RetrievalRepository,
        audit_repo: AuditRepository,
        embedding_provider: EmbeddingProvider,
        rerank_provider: RerankProvider,
        settings: Settings,
    ) -> None:
        self._session = session
        self._repo = retrieval_repo
        self._audit = audit_repo
        self._embedding = embedding_provider
        self._reranker = rerank_provider
        self._settings = settings

        self._dense_searcher = DenseSearcher(session)
        self._sparse_searcher = SparseSearcher(session)
        self._fusion = RRFFusion(k=60)

    async def _audit_event(
        self,
        event_type: AuditEventType,
        actor_id: uuid.UUID,
        target_id: uuid.UUID | None,
        target_type: str | None,
        outcome: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
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

    async def retrieve_knowledge(
        self,
        actor: UserContext,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 10,
        publication_status: str = "PUBLISHED",
    ) -> RetrievalResult:
        """
        Execute a knowledge retrieval operation.

        Idempotent: if identical query/mode/filters exists, returns
        the cached retrieval run and its candidates.

        Requires: KNOWLEDGE_READ permission.
        """
        from careintel.application.auth.permission_service import PermissionService

        PermissionService.check(actor, Permission.KNOWLEDGE_READ)

        # 1. Idempotency Check
        query_hash = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
        existing_orm = await self._repo.get_run_by_idempotency_key(
            case_id=None,
            query_hash=query_hash,
            corpus_version=None,
            search_mode=mode.value,
        )
        if existing_orm is not None:
            cand_orms = await self._repo.get_candidates_for_run(existing_orm.id)
            return RetrievalResult(
                metadata=self._to_metadata_domain(existing_orm),
                candidates=[self._to_candidate_domain(c) for c in cand_orms],
            )

        # 2. Embedding Version Lookup
        # Find the embedding version ID that matches the current provider
        # We need this for the dense search.
        from sqlalchemy import select

        from careintel.persistence.models.knowledge import EmbeddingVersionORM

        emb_version_orm = (
            await self._session.execute(
                select(EmbeddingVersionORM).where(
                    EmbeddingVersionORM.version_key == self._embedding.version_key
                )
            )
        ).scalar_one_or_none()
        emb_version_id = emb_version_orm.id if emb_version_orm else None

        # 3. Execution
        dense_results = []
        if mode in (SearchMode.DENSE, SearchMode.HYBRID) and emb_version_id:
            embed_res = await self._embedding.embed(query)
            dense_results = await self._dense_searcher.search(
                query_vector=embed_res.vector,
                embedding_version_id=emb_version_id,
                top_k=top_k * 2,  # Fetch more for fusion
                publication_status=publication_status,
            )

        sparse_results = []
        if mode in (SearchMode.SPARSE, SearchMode.HYBRID):
            sparse_results = await self._sparse_searcher.search(
                query_text=query,
                top_k=top_k * 2,
                publication_status=publication_status,
            )

        # 4. Fusion
        fused = self._fusion.fuse(dense_results, sparse_results, top_k=top_k)

        # 5. Reranking
        if fused:
            fused = await self._reranker.rerank(query, fused)

        # 6. Persistence
        run_orm = await self._repo.create_run(
            {
                "case_id": None,
                "query_hash": query_hash,
                "search_mode": mode.value,
                "corpus_version": None,
                "embedding_version_id": emb_version_id,
                "applied_filters": {"publication_status": publication_status},
                "status": RetrievalStatus.COMPLETED.value,
                "zero_result_reason": "NO_MATCHES" if not fused else None,
                "candidate_count": len(fused),
            }
        )

        cand_data = []
        for f in fused:
            cand_data.append(
                {
                    "retrieval_run_id": run_orm.id,
                    "source_type": "KNOWLEDGE_CHUNK",
                    "source_id": f.chunk_id,
                    "rank": f.rank,
                    "dense_score": f.dense_score,
                    "sparse_score": f.sparse_score,
                    "fusion_score": f.fusion_score,
                    "citation_locator": None,
                }
            )

        cand_orms = await self._repo.create_candidates(cand_data)
        await self._session.commit()

        # 7. Audit
        await self._audit_event(
            event_type=AuditEventType.RETRIEVAL_EXECUTED,
            actor_id=actor.id,
            target_id=run_orm.id,
            target_type="retrieval_run",
            outcome="success",
            detail={
                "search_mode": mode.value,
                "candidate_count": len(fused),
                "is_knowledge": True,
            },
        )

        return RetrievalResult(
            metadata=self._to_metadata_domain(run_orm),
            candidates=[self._to_candidate_domain(c) for c in cand_orms],
        )

    def _to_metadata_domain(self, orm: RetrievalRunORM) -> RetrievalMetadata:
        # Find embedding version key if we have ID
        # Since this is synchronous mapping, we handle None or fetch later if needed
        # For this design, we can store embedding_version_id temporarily or None
        # if we aren't joining it. The model asks for key.
        return RetrievalMetadata(
            retrieval_run_id=orm.id,
            query_hash=orm.query_hash,
            search_mode=SearchMode(orm.search_mode),
            corpus_version=orm.corpus_version,
            embedding_version_key=None,  # Not fully joined in this response
            applied_filters=dict(orm.applied_filters),
            status=RetrievalStatus(orm.status),
            zero_result_reason=orm.zero_result_reason,
            candidate_count=orm.candidate_count,
            created_at=orm.created_at,
        )

    @staticmethod
    def _to_candidate_domain(orm: RetrievalCandidateORM) -> RetrievalCandidate:
        from careintel.domain.retrieval.status import SourceType

        return RetrievalCandidate(
            candidate_id=orm.id,
            retrieval_run_id=orm.retrieval_run_id,
            source_type=SourceType(orm.source_type),
            source_id=orm.source_id,
            rank=orm.rank,
            dense_score=orm.dense_score,
            sparse_score=orm.sparse_score,
            fusion_score=orm.fusion_score,
            citation_locator=orm.citation_locator,
        )
