"""Case-scoped, version-pinned hybrid retrieval application service."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.application.retrieval.dense_search import DenseSearcher
from careintel.application.retrieval.fusion import RRFFusion
from careintel.application.retrieval.sparse_search import SparseSearcher
from careintel.core.correlation import get_correlation_id
from careintel.core.errors import NotFoundError, ValidationError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.domain.retrieval.models import (
    RetrievalCandidate,
    RetrievalMetadata,
    RetrievalResult,
)
from careintel.domain.retrieval.status import RetrievalStatus, SearchMode, SourceType
from careintel.infrastructure.embedding.port import EmbeddingProvider
from careintel.infrastructure.reranker.port import RerankProvider
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM
from careintel.persistence.models.retrieval import RetrievalCandidateORM, RetrievalRunORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.knowledge_repo import KnowledgeRepository
from careintel.persistence.repositories.retrieval_repo import RetrievalRepository


class RetrievalService:
    """Runs PostgreSQL lexical plus pgvector retrieval over trusted knowledge."""

    def __init__(
        self,
        session: AsyncSession,
        retrieval_repo: RetrievalRepository,
        knowledge_repo: KnowledgeRepository,
        case_repo: CaseRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
        embedding_provider: EmbeddingProvider,
        rerank_provider: RerankProvider,
    ) -> None:
        self._session = session
        self._repo = retrieval_repo
        self._knowledge = knowledge_repo
        self._cases = case_repo
        self._consent = consent_service
        self._audit = audit_repo
        self._embedding = embedding_provider
        self._reranker = rerank_provider
        self._dense_searcher = DenseSearcher(session)
        self._sparse_searcher = SparseSearcher(session)
        self._fusion = RRFFusion(k=60)

    async def _authorized_case(self, case_id: uuid.UUID, actor: UserContext) -> CaseORM:
        case = await self._cases.get_by_id(case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        PermissionService.check(
            actor,
            Permission.KNOWLEDGE_READ,
            facility_scope=case.facility_id,
        )
        await self._consent.require_active(
            case.synthetic_subject_id,
            ConsentPurpose.AI_ANALYSIS.value,
            "1.0",
        )
        return case

    async def _audit_event(
        self,
        actor_id: uuid.UUID,
        run_id: uuid.UUID,
        outcome: str,
        detail: dict[str, Any],
    ) -> None:
        await self._audit.append(
            AuditLogORM(
                event_type=AuditEventType.RETRIEVAL_EXECUTED.value,
                actor_id=actor_id,
                target_id=run_id,
                target_type="retrieval_run",
                correlation_id=get_correlation_id(),
                outcome=outcome,
                detail=detail,
            )
        )

    async def retrieve_knowledge(
        self,
        actor: UserContext,
        case_id: uuid.UUID,
        query: str,
        corpus_version: str,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 10,
    ) -> RetrievalResult:
        """Retrieve only active chunks from a published, pinned corpus."""
        await self._authorized_case(case_id, actor)
        normalized_query = " ".join(query.split())
        if not normalized_query:
            raise ValidationError("Retrieval query cannot be empty.")
        if not corpus_version.strip():
            raise ValidationError("corpus_version is required.")
        if top_k < 1 or top_k > 50:
            raise ValidationError("top_k must be between 1 and 50.")

        query_hash = hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()
        run = await self._repo.get_run_by_idempotency_key(
            case_id=case_id,
            query_hash=query_hash,
            corpus_version=corpus_version,
            search_mode=mode.value,
        )
        if run is not None and run.status in {
            RetrievalStatus.COMPLETED.value,
            RetrievalStatus.ZERO_RESULTS.value,
        }:
            return await self._result_for_run(run)

        embedding_version = None
        if mode in {SearchMode.DENSE, SearchMode.HYBRID}:
            embedding_version = await self._knowledge.get_embedding_version_by_key(
                self._embedding.version_key
            )
            if embedding_version is None:
                raise ValidationError("Active embedding version is not registered.")
            if embedding_version.dimension != self._embedding.dimension:
                raise ValidationError(
                    "Active embedding provider dimension does not match the registered version."
                )

        if run is None:
            run = await self._repo.create_run(
                {
                    "case_id": case_id,
                    "query_hash": query_hash,
                    "search_mode": mode.value,
                    "corpus_version": corpus_version,
                    "embedding_version_id": (
                        embedding_version.id if embedding_version is not None else None
                    ),
                    "applied_filters": {"publication_status": "PUBLISHED"},
                    "status": RetrievalStatus.FAILED.value,
                    "zero_result_reason": "EXECUTION_NOT_COMPLETED",
                    "candidate_count": 0,
                }
            )
            await self._session.commit()

        try:
            dense_results = []
            if embedding_version is not None:
                embedded = await self._embedding.embed(normalized_query)
                if (
                    embedded.version_key != embedding_version.version_key
                    or embedded.dimension != embedding_version.dimension
                    or len(embedded.vector) != embedding_version.dimension
                ):
                    raise ValidationError("Embedding result metadata is incompatible.")
                dense_results = await self._dense_searcher.search(
                    query_vector=embedded.vector,
                    embedding_version_id=embedding_version.id,
                    corpus_version=corpus_version,
                    top_k=top_k * 2,
                )

            sparse_results = []
            if mode in {SearchMode.SPARSE, SearchMode.HYBRID}:
                sparse_results = await self._sparse_searcher.search(
                    query_text=normalized_query,
                    corpus_version=corpus_version,
                    top_k=top_k * 2,
                )

            fused = self._fusion.fuse(dense_results, sparse_results, top_k=top_k)
            if fused:
                fused = await self._reranker.rerank(normalized_query, fused)

            chunks = await self._knowledge.get_published_chunks(
                [candidate.chunk_id for candidate in fused], corpus_version
            )
            chunk_map = {chunk.id: (chunk, version, source) for chunk, version, source in chunks}
            fused = [candidate for candidate in fused if candidate.chunk_id in chunk_map]

            await self._repo.delete_candidates_for_run(run.id)
            candidates = await self._repo.create_candidates(
                [
                    {
                        "retrieval_run_id": run.id,
                        "source_type": SourceType.KNOWLEDGE_CHUNK.value,
                        "source_id": candidate.chunk_id,
                        "rank": index,
                        "dense_score": candidate.dense_score,
                        "sparse_score": candidate.sparse_score,
                        "fusion_score": candidate.fusion_score,
                        "citation_locator": self._citation(*chunk_map[candidate.chunk_id]),
                    }
                    for index, candidate in enumerate(fused, start=1)
                ]
            )
            status = RetrievalStatus.COMPLETED if candidates else RetrievalStatus.ZERO_RESULTS
            updates = {
                "status": status.value,
                "zero_result_reason": None if candidates else "NO_MATCHES",
                "candidate_count": len(candidates),
                "embedding_version_id": (
                    embedding_version.id if embedding_version is not None else None
                ),
            }
            await self._repo.update_run(run.id, updates)
            await self._session.commit()
            for key, value in updates.items():
                setattr(run, key, value)
            await self._audit_event(
                actor.id,
                run.id,
                "SUCCESS",
                {"search_mode": mode.value, "candidate_count": len(candidates)},
            )
            return RetrievalResult(
                metadata=self._to_metadata_domain(
                    run,
                    embedding_version.version_key if embedding_version is not None else None,
                ),
                candidates=[self._to_candidate_domain(item) for item in candidates],
            )
        except Exception as exc:
            await self._session.rollback()
            await self._repo.update_run(
                run.id,
                {
                    "status": RetrievalStatus.FAILED.value,
                    "zero_result_reason": type(exc).__name__,
                    "candidate_count": 0,
                },
            )
            await self._session.commit()
            await self._audit_event(
                actor.id,
                run.id,
                "FAILURE",
                {"search_mode": mode.value, "error_category": type(exc).__name__},
            )
            raise

    async def get_result(
        self, actor: UserContext, case_id: uuid.UUID, run_id: uuid.UUID
    ) -> RetrievalResult:
        await self._authorized_case(case_id, actor)
        run = await self._repo.get_run(run_id)
        if run is None or run.case_id != case_id:
            raise NotFoundError("Retrieval run not found for case.")
        return await self._result_for_run(run)

    async def _result_for_run(self, run: RetrievalRunORM) -> RetrievalResult:
        candidates = await self._repo.get_candidates_for_run(run.id)
        embedding_key = None
        if run.embedding_version_id is not None:
            version = await self._knowledge.get_embedding_version_by_key(
                self._embedding.version_key
            )
            if version is not None and version.id == run.embedding_version_id:
                embedding_key = version.version_key
        return RetrievalResult(
            metadata=self._to_metadata_domain(run, embedding_key),
            candidates=[self._to_candidate_domain(item) for item in candidates],
        )

    @staticmethod
    def _citation(chunk: Any, version: Any, source: Any) -> str:
        return f"{source.name}; version {version.version_key}; chunk {chunk.chunk_index}"

    @staticmethod
    def _to_metadata_domain(
        orm: RetrievalRunORM, embedding_version_key: str | None
    ) -> RetrievalMetadata:
        return RetrievalMetadata(
            retrieval_run_id=orm.id,
            query_hash=orm.query_hash,
            search_mode=SearchMode(orm.search_mode),
            corpus_version=orm.corpus_version,
            embedding_version_key=embedding_version_key,
            applied_filters=dict(orm.applied_filters),
            status=RetrievalStatus(orm.status),
            zero_result_reason=orm.zero_result_reason,
            candidate_count=orm.candidate_count,
            created_at=orm.created_at,
        )

    @staticmethod
    def _to_candidate_domain(orm: RetrievalCandidateORM) -> RetrievalCandidate:
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
