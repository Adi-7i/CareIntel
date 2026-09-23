"""Case-scoped retrieval persistence and failure tests."""

import datetime
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from careintel.application.retrieval.dense_search import DenseSearchResult
from careintel.application.retrieval.retrieval_service import RetrievalService
from careintel.application.retrieval.sparse_search import SparseSearchResult
from careintel.core.errors import AuthorizationError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.retrieval.status import RetrievalStatus
from careintel.infrastructure.embedding.port import EmbeddingResult
from careintel.infrastructure.reranker.noop_reranker import NoOpReranker


def _actor(facility_id: uuid.UUID) -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"reviewer"},
        permissions={Permission.KNOWLEDGE_READ.value},
        role_facilities={"reviewer": facility_id},
    )


def _service() -> tuple[RetrievalService, dict[str, AsyncMock | object]]:
    session = AsyncMock()
    retrieval = AsyncMock()
    knowledge = AsyncMock()
    cases = AsyncMock()
    consent = AsyncMock()
    audit = AsyncMock()
    embedding = SimpleNamespace(version_key="synthetic-1536-v1", dimension=1536)
    embedding.embed = AsyncMock(
        return_value=EmbeddingResult(
            vector=[0.0] * 1536,
            provider="synthetic",
            model="synthetic",
            dimension=1536,
            version_key="synthetic-1536-v1",
        )
    )
    service = RetrievalService(
        session,
        retrieval,
        knowledge,
        cases,
        consent,
        audit,
        embedding,
        NoOpReranker(),
    )
    return service, {
        "session": session,
        "retrieval": retrieval,
        "knowledge": knowledge,
        "cases": cases,
        "consent": consent,
        "audit": audit,
        "embedding": embedding,
    }


@pytest.mark.asyncio
async def test_hybrid_retrieval_persists_pinned_provenance() -> None:
    service, deps = _service()
    facility_id = uuid.uuid4()
    case_id = uuid.uuid4()
    chunk_id = uuid.uuid4()
    run_id = uuid.uuid4()
    deps["cases"].get_by_id.return_value = SimpleNamespace(  # type: ignore[union-attr]
        id=case_id, facility_id=facility_id, synthetic_subject_id=uuid.uuid4()
    )
    deps["retrieval"].get_run_by_idempotency_key.return_value = None  # type: ignore[union-attr]
    run = SimpleNamespace(
        id=run_id,
        case_id=case_id,
        query_hash="hash",
        search_mode="HYBRID",
        corpus_version="synthetic-v1",
        embedding_version_id=None,
        applied_filters={"publication_status": "PUBLISHED"},
        status="FAILED",
        zero_result_reason=None,
        candidate_count=0,
        created_at=datetime.datetime.now(datetime.UTC),
    )
    deps["retrieval"].create_run.return_value = run  # type: ignore[union-attr]
    embedding_version = SimpleNamespace(
        id=uuid.uuid4(), version_key="synthetic-1536-v1", dimension=1536
    )
    deps["knowledge"].get_embedding_version_by_key.return_value = embedding_version  # type: ignore[union-attr]
    chunk = SimpleNamespace(id=chunk_id, content="synthetic", chunk_index=2)
    version = SimpleNamespace(version_key="v1")
    source = SimpleNamespace(name="Synthetic approved source")
    deps["knowledge"].get_published_chunks.return_value = [(chunk, version, source)]  # type: ignore[union-attr]

    service._dense_searcher.search = AsyncMock(return_value=[DenseSearchResult(chunk_id, 0.8)])
    service._sparse_searcher.search = AsyncMock(return_value=[SparseSearchResult(chunk_id, 0.4)])

    async def create_candidates(data: list[dict[str, object]]) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(id=uuid.uuid4(), created_at=run.created_at, **item) for item in data
        ]

    deps["retrieval"].create_candidates.side_effect = create_candidates  # type: ignore[union-attr]
    result = await service.retrieve_knowledge(
        _actor(facility_id), case_id, "synthetic query", "synthetic-v1"
    )

    assert result.metadata.status == RetrievalStatus.COMPLETED
    assert result.metadata.corpus_version == "synthetic-v1"
    assert result.candidates[0].source_id == chunk_id
    assert result.candidates[0].citation_locator == (
        "Synthetic approved source; version v1; chunk 2"
    )
    assert service._dense_searcher.search.await_args.kwargs["corpus_version"] == "synthetic-v1"
    assert service._sparse_searcher.search.await_args.kwargs["corpus_version"] == "synthetic-v1"


@pytest.mark.asyncio
async def test_retrieval_failure_is_persisted_without_provider_message() -> None:
    service, deps = _service()
    facility_id = uuid.uuid4()
    case_id = uuid.uuid4()
    deps["cases"].get_by_id.return_value = SimpleNamespace(  # type: ignore[union-attr]
        id=case_id, facility_id=facility_id, synthetic_subject_id=uuid.uuid4()
    )
    deps["retrieval"].get_run_by_idempotency_key.return_value = None  # type: ignore[union-attr]
    deps["knowledge"].get_embedding_version_by_key.return_value = SimpleNamespace(  # type: ignore[union-attr]
        id=uuid.uuid4(), version_key="synthetic-1536-v1", dimension=1536
    )
    run = SimpleNamespace(id=uuid.uuid4())
    deps["retrieval"].create_run.return_value = run  # type: ignore[union-attr]
    deps["embedding"].embed.side_effect = RuntimeError("sensitive provider payload")  # type: ignore[union-attr]

    with pytest.raises(RuntimeError):
        await service.retrieve_knowledge(
            _actor(facility_id), case_id, "synthetic query", "synthetic-v1"
        )

    failure_updates = [
        call.args[1]
        for call in deps["retrieval"].update_run.await_args_list  # type: ignore[union-attr]
        if call.args[1]["status"] == "FAILED"
    ]
    assert failure_updates[-1]["zero_result_reason"] == "RuntimeError"
    assert "sensitive" not in str(failure_updates[-1])


@pytest.mark.asyncio
async def test_retrieval_denies_cross_facility_access_before_embedding() -> None:
    service, deps = _service()
    deps["cases"].get_by_id.return_value = SimpleNamespace(  # type: ignore[union-attr]
        id=uuid.uuid4(), facility_id=uuid.uuid4(), synthetic_subject_id=uuid.uuid4()
    )

    with pytest.raises(AuthorizationError):
        await service.retrieve_knowledge(
            _actor(uuid.uuid4()), uuid.uuid4(), "synthetic", "synthetic-v1"
        )

    deps["embedding"].embed.assert_not_awaited()  # type: ignore[union-attr]
