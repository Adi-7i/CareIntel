"""
Unit tests for ProcessingService.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from careintel.application.processing.processing_service import ProcessingService
from careintel.core.errors import CareIntelError
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
    )


@pytest.fixture
def mocks() -> dict[str, AsyncMock]:
    return {
        "doc_processor": AsyncMock(),
        "speech_processor": AsyncMock(),
        "lang_processor": AsyncMock(),
        "ext_processor": AsyncMock(),
    }


@pytest.fixture
def service(mocks: dict[str, AsyncMock]) -> ProcessingService:
    return ProcessingService(
        document_processor=mocks["doc_processor"],
        speech_processor=mocks["speech_processor"],
        language_processor=mocks["lang_processor"],
        extraction_processor=mocks["ext_processor"],
    )


@pytest.mark.asyncio
async def test_trigger_document_ocr(
    service: ProcessingService, mocks: dict[str, AsyncMock], user: UserContext
) -> None:
    evidence_id = uuid.uuid4()
    run_id = uuid.uuid4()
    mocks["doc_processor"].process.return_value = run_id

    command = TriggerProcessingCommand(
        evidence_id=evidence_id, processor_type=ProcessorType.DOCUMENT_OCR
    )

    result = await service.trigger_processing(command, user, "corr")
    assert result == run_id
    mocks["doc_processor"].process.assert_called_once_with(evidence_id, user, "corr")


@pytest.mark.asyncio
async def test_trigger_language_norm(
    service: ProcessingService, mocks: dict[str, AsyncMock], user: UserContext
) -> None:
    evidence_id = uuid.uuid4()
    run_id = uuid.uuid4()
    mocks["lang_processor"].process.return_value = run_id

    command = TriggerProcessingCommand(
        evidence_id=evidence_id,
        processor_type=ProcessorType.LANGUAGE_NORMALIZATION,
        parameters={"text": "hello", "target_language": "fr"},
    )

    result = await service.trigger_processing(command, user, "corr")
    assert result == run_id
    mocks["lang_processor"].process.assert_called_once_with(
        evidence_id, "hello", user, "corr", target_language="fr"
    )


@pytest.mark.asyncio
async def test_trigger_unsupported(
    service: ProcessingService, mocks: dict[str, AsyncMock], user: UserContext
) -> None:
    command = TriggerProcessingCommand(
        evidence_id=uuid.uuid4(),
        processor_type="unsupported",  # type: ignore
    )

    with pytest.raises(CareIntelError):
        await service.trigger_processing(command, user, "corr")
