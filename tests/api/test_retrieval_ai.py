"""API contracts for case-scoped retrieval and advisory AI."""

import datetime
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from careintel.application.ai.ai_workflow_service import AIWorkflowService
from careintel.application.retrieval.retrieval_service import RetrievalService
from careintel.domain.ai.models import AIDraft
from careintel.domain.ai.status import DraftReviewerStatus, ValidationStatus
from careintel.domain.auth.models import UserContext
from careintel.domain.retrieval.models import RetrievalMetadata, RetrievalResult
from careintel.domain.retrieval.status import RetrievalStatus, SearchMode


@pytest_asyncio.fixture
async def retrieval_ai_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    from careintel.api.deps import (
        get_ai_workflow_service,
        get_current_user,
        get_retrieval_service,
    )

    user = UserContext(id=uuid.uuid4(), is_active=True)
    app.state.test_retrieval_service = AsyncMock(spec=RetrievalService)
    app.state.test_ai_service = AsyncMock(spec=AIWorkflowService)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_retrieval_service] = lambda: app.state.test_retrieval_service
    app.dependency_overrides[get_ai_workflow_service] = lambda: app.state.test_ai_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.api
async def test_retrieval_endpoint_returns_persisted_state(
    app: FastAPI, retrieval_ai_client: AsyncClient
) -> None:
    case_id = uuid.uuid4()
    run_id = uuid.uuid4()
    app.state.test_retrieval_service.retrieve_knowledge.return_value = RetrievalResult(
        metadata=RetrievalMetadata(
            retrieval_run_id=run_id,
            query_hash="a" * 64,
            search_mode=SearchMode.HYBRID,
            corpus_version="synthetic-v1",
            embedding_version_key="synthetic-1536-v1",
            applied_filters={"publication_status": "PUBLISHED"},
            candidate_count=0,
            status=RetrievalStatus.ZERO_RESULTS,
            zero_result_reason="NO_MATCHES",
            created_at=datetime.datetime.now(datetime.UTC),
        )
    )

    response = await retrieval_ai_client.post(
        f"/api/v1/cases/{case_id}/retrieval",
        json={
            "query": "synthetic query",
            "corpus_version": "synthetic-v1",
            "search_mode": "HYBRID",
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["status"] == "ZERO_RESULTS"
    assert response.json()["metadata"]["retrieval_run_id"] == str(run_id)


@pytest.mark.api
async def test_ai_endpoint_returns_advisory_draft_only(
    app: FastAPI, retrieval_ai_client: AsyncClient
) -> None:
    case_id = uuid.uuid4()
    retrieval_id = uuid.uuid4()
    draft_id = uuid.uuid4()
    app.state.test_ai_service.execute_advisory.return_value = AIDraft(
        draft_id=draft_id,
        ai_run_id=uuid.uuid4(),
        content={
            "summary": "Synthetic summary.",
            "claims": [],
            "missing_information_ids": [],
            "limitations": ["Human review required."],
        },
        validation_status=ValidationStatus.ACCEPTED,
        validation_errors=[],
        claim_provenance=[],
        reviewer_status=DraftReviewerStatus.DRAFT,
        reviewer_id=None,
        reviewed_at=None,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    response = await retrieval_ai_client.post(
        f"/api/v1/cases/{case_id}/ai/drafts",
        json={
            "retrieval_run_id": str(retrieval_id),
            "task_type": "evidence_summary",
        },
    )

    assert response.status_code == 200
    assert response.json()["draft_id"] == str(draft_id)
    assert response.json()["reviewer_status"] == "DRAFT"
    assert "approval" not in response.json()
