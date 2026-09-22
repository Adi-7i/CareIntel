"""
Unit tests for ProcessingService.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from careintel.application.processing.processing_service import ProcessingService
from careintel.domain.auth.models import UserContext
from careintel.domain.processing.processing_commands import TriggerProcessingCommand
from careintel.domain.processing.processor_type import ProcessorType


@pytest.fixture
def user() -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"doctor"},
        permissions={"processing:write"},
        role_facilities={"doctor": None},
    )


@pytest.fixture
def mocks() -> dict[str, AsyncMock]:
    return {
        "doc_processor": AsyncMock(),
        "speech_processor": AsyncMock(),
        "lang_processor": AsyncMock(),
        "ext_processor": AsyncMock(),
        "task_service": AsyncMock(),
        "evidence_repo": AsyncMock(),
        "case_repo": AsyncMock(),
        "outbox_repo": AsyncMock(),
    }


@pytest.fixture
def service(mocks: dict[str, AsyncMock]) -> ProcessingService:
    return ProcessingService(
        document_processor=mocks["doc_processor"],
        speech_processor=mocks["speech_processor"],
        language_processor=mocks["lang_processor"],
        extraction_processor=mocks["ext_processor"],
        task_service=mocks["task_service"],
        evidence_repo=mocks["evidence_repo"],
        case_repo=mocks["case_repo"],
        outbox_repo=mocks["outbox_repo"],
    )


@pytest.mark.asyncio
async def test_trigger_document_ocr(
    service: ProcessingService, mocks: dict[str, AsyncMock], user: UserContext
) -> None:
    evidence_id = uuid.uuid4()
    run_id = uuid.uuid4()

    task_mock = AsyncMock()
    task_mock.id = run_id
    mocks["task_service"].get_or_create_task.return_value = task_mock

    command = TriggerProcessingCommand(
        evidence_id=evidence_id, processor_type=ProcessorType.DOCUMENT_OCR
    )

    result = await service.trigger_processing(command, user, "corr")
    assert result == run_id
    mocks["task_service"].get_or_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_language_norm(
    service: ProcessingService, mocks: dict[str, AsyncMock], user: UserContext
) -> None:
    evidence_id = uuid.uuid4()
    run_id = uuid.uuid4()

    task_mock = AsyncMock()
    task_mock.id = run_id
    mocks["task_service"].get_or_create_task.return_value = task_mock

    command = TriggerProcessingCommand(
        evidence_id=evidence_id, processor_type=ProcessorType.LANGUAGE_NORMALIZATION
    )

    result = await service.trigger_processing(command, user, "corr")
    assert result == run_id
    mocks["task_service"].get_or_create_task.assert_called_once()


def test_unsupported_processor_type_rejected() -> None:
    with pytest.raises(ValueError):
        ProcessorType("unsupported")
