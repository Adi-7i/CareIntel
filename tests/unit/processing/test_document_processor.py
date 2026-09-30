"""
Unit tests for DocumentProcessor.
"""

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

from careintel.application.processing.document_processor import DocumentProcessor
from careintel.core.config import Settings
from careintel.core.errors import (
    CareIntelError,
    ValidationError,
)
from careintel.domain.auth.models import UserContext
from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.evidence.states import EvidenceState
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.infrastructure.ocr.port import OcrResult
from careintel.persistence.models.evidence import EvidenceORM
from careintel.persistence.models.processing import ProcessingRunORM


@pytest.fixture
def user() -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"doctor"},
        permissions={"processing:write"},
    )


@pytest.fixture
def evidence() -> EvidenceORM:
    return EvidenceORM(
        id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        modality=EvidenceModality.DOCUMENT.value,
        state=EvidenceState.READY.value,
        original_filename="test.pdf",
        content_type="application/pdf",
        size_bytes=1000,
        storage_key="test-key",
        created_by=uuid.uuid4(),
    )


@pytest.fixture
def mocks() -> dict[str, AsyncMock]:
    return {
        "access_guard": AsyncMock(),
        "processing_repo": AsyncMock(),
        "outbox_repo": AsyncMock(),
        "blob_storage": AsyncMock(),
        "ocr_provider": AsyncMock(),
    }


@pytest.fixture
def processor(mocks: dict[str, AsyncMock]) -> DocumentProcessor:
    settings = Settings(
        database_url=SecretStr("postgresql+asyncpg://mock"),
        secret_key=SecretStr("mock"),
        jwt_secret_key=SecretStr("mock"),
        ocr_provider="demo",
        ocr_temp_workspace="/tmp/test_ocr",
    )
    return DocumentProcessor(
        settings=settings,
        access_guard=mocks["access_guard"],
        processing_repo=mocks["processing_repo"],
        outbox_repo=mocks["outbox_repo"],
        blob_storage=mocks["blob_storage"],
        ocr_provider=mocks["ocr_provider"],
    )


@pytest.mark.asyncio
async def test_process_success(
    processor: DocumentProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["access_guard"].require_ready_evidence.return_value = evidence
    mocks["processing_repo"].get_run_by_idempotency_key.return_value = None

    async def async_generator() -> AsyncGenerator[bytes, None]:
        yield b"fake pdf data"

    mocks["blob_storage"].download = MagicMock(return_value=async_generator())
    mocks["ocr_provider"].process_document.return_value = OcrResult(
        pages=[], regions=[], provider_version="test"
    )

    run_id = await processor.process(evidence.id, user, "corr-1")

    assert run_id is not None
    mocks["processing_repo"].add_run.assert_called_once()
    added_run = mocks["processing_repo"].add_run.call_args[0][0]
    assert added_run.status == ProcessingStatus.COMPLETED.value
    mocks["outbox_repo"].append.assert_called_once()


@pytest.mark.asyncio
async def test_process_idempotency(
    processor: DocumentProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["access_guard"].require_ready_evidence.return_value = evidence

    existing_run = ProcessingRunORM(
        id=uuid.uuid4(),
        evidence_id=evidence.id,
        processor_type="document_ocr",
        provider="demo",
        status=ProcessingStatus.COMPLETED.value,
        config_version="v1",
    )
    mocks["processing_repo"].get_run_by_idempotency_key.return_value = existing_run

    run_id = await processor.process(evidence.id, user, "corr-1")

    assert run_id == existing_run.id
    mocks["blob_storage"].download.assert_not_called()


@pytest.mark.asyncio
async def test_process_not_ready(
    processor: DocumentProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["access_guard"].require_ready_evidence.side_effect = ValidationError(
        "Evidence must be READY"
    )

    with pytest.raises(CareIntelError):
        await processor.process(evidence.id, user, "corr-1")


@pytest.mark.asyncio
async def test_process_invalid_modality(
    processor: DocumentProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    evidence.modality = EvidenceModality.AUDIO.value
    mocks["access_guard"].require_ready_evidence.return_value = evidence

    with pytest.raises(CareIntelError):
        await processor.process(evidence.id, user, "corr-1")


@pytest.mark.asyncio
async def test_process_ocr_failure(
    processor: DocumentProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["access_guard"].require_ready_evidence.return_value = evidence
    mocks["processing_repo"].get_run_by_idempotency_key.return_value = None

    async def async_generator() -> AsyncGenerator[bytes, None]:
        yield b"fake pdf data"

    mocks["blob_storage"].download = MagicMock(return_value=async_generator())
    mocks["ocr_provider"].process_document.side_effect = Exception("OCR Engine Failed")

    run_id = await processor.process(evidence.id, user, "corr-1")

    assert run_id is not None
    added_run = mocks["processing_repo"].add_run.call_args[0][0]
    assert added_run.status == ProcessingStatus.FAILED.value
    assert added_run.failure_reason == "Exception"
    mocks["outbox_repo"].append.assert_called_once()
