"""Persisted AI execution, validation, policy, and failure tests."""

import datetime
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from careintel.application.ai.ai_service import AIService
from careintel.application.ai.policy_service import PolicyService
from careintel.domain.ai.models import AITaskConfig, ContextPassage, SafeContext
from careintel.domain.ai.status import ContentOrigin, TaskType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.infrastructure.ai.port import LLMProviderError, LLMResult


def _actor() -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"reviewer"},
        permissions={Permission.AI_WRITE.value},
        role_facilities={"reviewer": None},
    )


def _context(source_id: uuid.UUID) -> SafeContext:
    return SafeContext(
        system_instructions="trusted",
        task_instructions="bounded",
        output_schema={"type": "object"},
        policy_constraints=["Human review required"],
        knowledge_passages=[
            ContextPassage("synthetic", ContentOrigin.KNOWLEDGE, source_id, "synthetic")
        ],
        patient_evidence=[],
        stt_transcripts=[],
        ocr_content=[],
        extracted_facts=[],
        timeline_events=[],
        missing_information=[],
        conflicting_information=[],
        retrieval_metadata=None,
    )


def _config() -> AITaskConfig:
    return AITaskConfig(
        task_type=TaskType.EVIDENCE_SUMMARY,
        provider="synthetic",
        model="synthetic",
        prompt_version="v1",
        schema_version="v1",
        timeout_seconds=1,
    )


def _service(provider: AsyncMock) -> tuple[AIService, AsyncMock, AsyncMock]:
    session = AsyncMock()
    repo = AsyncMock()
    audit = AsyncMock()
    run_id = uuid.uuid4()
    repo.get_run_by_idempotency_key.return_value = None
    repo.create_run.return_value = SimpleNamespace(id=run_id)
    stored: dict[str, SimpleNamespace] = {}

    async def create_draft(data: dict[str, object]) -> SimpleNamespace:
        draft = SimpleNamespace(
            id=uuid.uuid4(),
            ai_run_id=run_id,
            content_json=data["content_json"],
            validation_status=data["validation_status"],
            validation_errors=data["validation_errors"],
            provenance_json=data["provenance_json"],
            reviewer_status=data["reviewer_status"],
            reviewer_id=None,
            reviewed_at=None,
            created_at=datetime.datetime.now(datetime.UTC),
        )
        stored["draft"] = draft
        return draft

    repo.create_draft.side_effect = create_draft
    repo.get_draft.side_effect = lambda _draft_id: stored["draft"]
    service = AIService(session, repo, audit, provider, PolicyService())
    return service, repo, session


@pytest.mark.asyncio
async def test_ai_service_persists_validated_advisory_draft() -> None:
    source_id = uuid.uuid4()
    provider = AsyncMock()
    provider.generate_structured.return_value = LLMResult(
        raw_response="synthetic-response",
        parsed_content={
            "summary": "Synthetic evidence summary.",
            "claims": [
                {
                    "text": "Synthetic source is present.",
                    "status": "SUPPORTED",
                    "supporting_source_ids": [str(source_id)],
                }
            ],
            "missing_information_ids": [],
            "limitations": ["Human review required."],
        },
        finish_reason="stop",
        prompt_tokens=2,
        completion_tokens=3,
    )
    service, repo, _session = _service(provider)

    draft = await service.execute_task(_actor(), uuid.uuid4(), _config(), _context(source_id))

    assert draft.validation_status.value == "ACCEPTED"
    assert draft.reviewer_status.value == "DRAFT"
    assert draft.claim_provenance[0].supporting_source_ids == [source_id]
    assert repo.create_policy_decisions.await_count == 1
    completed = [
        call.args[1]
        for call in repo.update_run.await_args_list
        if call.args[1].get("status") == "COMPLETED"
    ]
    assert len(completed) == 1
    assert completed[0]["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_ai_service_persists_malformed_output_as_rejected() -> None:
    provider = AsyncMock()
    provider.generate_structured.return_value = LLMResult(
        raw_response="{}",
        parsed_content={},
        finish_reason="stop",
        prompt_tokens=1,
        completion_tokens=1,
    )
    service, repo, _session = _service(provider)

    draft = await service.execute_task(_actor(), uuid.uuid4(), _config(), _context(uuid.uuid4()))

    assert draft.validation_status.value == "REJECTED"
    assert draft.reviewer_status.value == "REJECTED"
    rejected = [
        call.args[1]
        for call in repo.update_run.await_args_list
        if call.args[1].get("status") == "REJECTED"
    ]
    assert len(rejected) == 1
    assert rejected[0]["failure_reason"] == "StructuredOutputRejected"
    repo.create_policy_decisions.assert_not_awaited()


@pytest.mark.asyncio
async def test_ai_service_records_sanitized_provider_failure() -> None:
    provider = AsyncMock()
    provider.generate_structured.side_effect = LLMProviderError("secret provider detail")
    service, repo, session = _service(provider)

    with pytest.raises(LLMProviderError):
        await service.execute_task(_actor(), uuid.uuid4(), _config(), _context(uuid.uuid4()))

    failed = [
        call.args[1]
        for call in repo.update_run.await_args_list
        if call.args[1].get("status") == "FAILED"
    ]
    assert len(failed) == 1
    assert failed[0]["failure_reason"] == "LLMProviderError"
    assert "secret" not in str(failed[0])
    session.commit.assert_awaited()
