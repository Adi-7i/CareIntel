"""
Unit tests for SpeechProcessor.
"""

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

from careintel.application.processing.speech_processor import SpeechProcessor
from careintel.core.config import Settings
from careintel.core.errors import (
    CareIntelError,
)
from careintel.domain.auth.models import UserContext
from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.evidence.states import EvidenceState
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.infrastructure.stt.port import SpeechResult
from careintel.persistence.models.evidence import EvidenceORM


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
        modality=EvidenceModality.AUDIO.value,
        state=EvidenceState.READY.value,
        original_filename="test.wav",
        content_type="audio/wav",
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
        "speech_provider": AsyncMock(),
    }


@pytest.fixture
def processor(mocks: dict[str, AsyncMock]) -> SpeechProcessor:
    settings = Settings(
        database_url=SecretStr("postgresql+asyncpg://mock"),
        secret_key=SecretStr("mock"),
        jwt_secret_key=SecretStr("mock"),
        stt_provider="demo",
    )
    return SpeechProcessor(
        settings=settings,
        access_guard=mocks["access_guard"],
        processing_repo=mocks["processing_repo"],
        outbox_repo=mocks["outbox_repo"],
        blob_storage=mocks["blob_storage"],
        speech_provider=mocks["speech_provider"],
    )


@pytest.mark.asyncio
async def test_process_success(
    processor: SpeechProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["access_guard"].require_ready_evidence.return_value = evidence
    mocks["processing_repo"].get_run_by_idempotency_key.return_value = None

    async def async_generator() -> AsyncGenerator[bytes, None]:
        yield b"fake audio data"

    mocks["blob_storage"].download = MagicMock(return_value=async_generator())
    mocks["speech_provider"].process_audio.return_value = SpeechResult(
        segments=[], provider_version="test"
    )

    run_id = await processor.process(evidence.id, user, "corr-1")

    assert run_id is not None
    mocks["processing_repo"].add_run.assert_called_once()
    added_run = mocks["processing_repo"].add_run.call_args[0][0]
    assert added_run.status == ProcessingStatus.COMPLETED.value
    mocks["outbox_repo"].append.assert_called_once()


@pytest.mark.asyncio
async def test_process_invalid_modality(
    processor: SpeechProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    evidence.modality = EvidenceModality.DOCUMENT.value
    mocks["access_guard"].require_ready_evidence.return_value = evidence

    with pytest.raises(CareIntelError):
        await processor.process(evidence.id, user, "corr-1")
