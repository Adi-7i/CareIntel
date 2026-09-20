"""
Unit tests for LanguageProcessor.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from careintel.application.processing.language_processor import LanguageProcessor
from careintel.core.config import Settings
from careintel.domain.auth.models import UserContext
from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.evidence.states import EvidenceState
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.infrastructure.language.port import LanguageDetectionResult
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
        modality=EvidenceModality.TEXT.value,
        state=EvidenceState.READY.value,
        created_by=uuid.uuid4(),
    )


@pytest.fixture
def mocks() -> dict[str, AsyncMock]:
    return {
        "evidence_repo": AsyncMock(),
        "processing_repo": AsyncMock(),
        "outbox_repo": AsyncMock(),
        "language_provider": AsyncMock(),
        "translation_provider": AsyncMock(),
    }


@pytest.fixture
def processor(mocks: dict[str, AsyncMock]) -> LanguageProcessor:
    settings = Settings(
        database_url=SecretStr("mock"),
        secret_key=SecretStr("mock"),
        jwt_secret_key=SecretStr("mock"),
        language_detection_provider="demo",
        translation_provider="demo",
    )
    return LanguageProcessor(
        settings=settings,
        evidence_repo=mocks["evidence_repo"],
        processing_repo=mocks["processing_repo"],
        outbox_repo=mocks["outbox_repo"],
        language_provider=mocks["language_provider"],
        translation_provider=mocks["translation_provider"],
    )


@pytest.mark.asyncio
async def test_process_no_translation_needed(
    processor: LanguageProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["evidence_repo"].get_by_id.return_value = evidence
    mocks["processing_repo"].get_run_by_idempotency_key.return_value = None
    mocks["language_provider"].detect_language.return_value = [LanguageDetectionResult("en", 0.99)]

    run_id = await processor.process(evidence.id, "Hello World", user, "corr")

    assert run_id is not None
    mocks["processing_repo"].add_run.assert_called_once()
    added_run = mocks["processing_repo"].add_run.call_args[0][0]
    assert added_run.status == ProcessingStatus.COMPLETED.value
    mocks["translation_provider"].translate.assert_not_called()

    # Check that LanguageResultORM was added
    result_orm = mocks["processing_repo"].session.add.call_args[0][0]
    assert result_orm.detected_language == "en"
    assert result_orm.translation_text is None


@pytest.mark.asyncio
async def test_process_translation_needed(
    processor: LanguageProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["evidence_repo"].get_by_id.return_value = evidence
    mocks["processing_repo"].get_run_by_idempotency_key.return_value = None
    mocks["language_provider"].detect_language.return_value = [LanguageDetectionResult("fr", 0.95)]
    mocks["translation_provider"].translate.return_value = "Hello"

    await processor.process(evidence.id, "Bonjour", user, "corr")

    mocks["translation_provider"].translate.assert_called_once_with("Bonjour", "fr", "en")

    result_orm = mocks["processing_repo"].session.add.call_args[0][0]
    assert result_orm.detected_language == "fr"
    assert result_orm.translation_text == "Hello"


@pytest.mark.asyncio
async def test_process_provider_error(
    processor: LanguageProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["evidence_repo"].get_by_id.return_value = evidence
    mocks["processing_repo"].get_run_by_idempotency_key.return_value = None
    mocks["language_provider"].detect_language.side_effect = Exception("API Down")

    await processor.process(evidence.id, "Bonjour", user, "corr")

    added_run = mocks["processing_repo"].add_run.call_args[0][0]
    assert added_run.status == ProcessingStatus.FAILED.value
    assert "API Down" in added_run.failure_reason
