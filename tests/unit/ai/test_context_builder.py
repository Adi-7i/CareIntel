"""Case isolation tests for persisted AI context construction."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from careintel.application.ai.context_builder import AIContextBuilder
from careintel.core.errors import NotFoundError
from careintel.domain.ai.status import TaskType


@pytest.mark.asyncio
async def test_context_builder_rejects_retrieval_run_from_another_case() -> None:
    case_a = uuid.uuid4()
    retrieval_repo = AsyncMock()
    retrieval_repo.get_run.return_value = SimpleNamespace(
        id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        status="COMPLETED",
        corpus_version="synthetic-v1",
    )
    evidence_repo = AsyncMock()
    builder = AIContextBuilder(
        retrieval_repo=retrieval_repo,
        knowledge_repo=AsyncMock(),
        evidence_repo=evidence_repo,
        text_repo=AsyncMock(),
        processing_repo=AsyncMock(),
        structuring_repo=AsyncMock(),
    )

    with pytest.raises(NotFoundError):
        await builder.build(case_a, uuid.uuid4(), TaskType.EVIDENCE_SUMMARY)

    evidence_repo.get_by_case_id.assert_not_awaited()
