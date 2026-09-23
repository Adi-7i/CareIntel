"""Consent-bound evidence intake regression tests."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from careintel.application.evidence.evidence_service import EvidenceService
from careintel.application.evidence.file_validator import FileValidator
from careintel.core.errors import ConsentError
from careintel.infrastructure.scanner.noop_scanner import NoOpScanner
from careintel.infrastructure.storage.fake_provider import FakeBlobProvider


def _service(consent: object | None) -> EvidenceService:
    consent_repo = AsyncMock()
    consent_repo.get_by_id.return_value = consent
    return EvidenceService(
        case_repo=AsyncMock(),
        encounter_repo=AsyncMock(),
        consent_repo=consent_repo,
        evidence_repo=AsyncMock(),
        text_repo=AsyncMock(),
        history_repo=AsyncMock(),
        outbox_repo=AsyncMock(),
        audit_repo=AsyncMock(),
        case_service=AsyncMock(),
        blob_provider=FakeBlobProvider(),
        scanner=NoOpScanner(),
        file_validator=FileValidator([".pdf"], 1024),
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_evidence_intake_rejects_missing_consent() -> None:
    case = SimpleNamespace(synthetic_subject_id=uuid.uuid4())

    with pytest.raises(ConsentError, match="No active consent"):
        await _service(None)._require_data_processing_consent(uuid.uuid4(), case)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_evidence_intake_rejects_withdrawn_consent() -> None:
    subject_id = uuid.uuid4()
    consent = SimpleNamespace(
        id=uuid.uuid4(),
        subject_id=subject_id,
        purpose="data_processing",
        notice_version="1.0",
        state="WITHDRAWN",
    )
    case = SimpleNamespace(synthetic_subject_id=subject_id)

    with pytest.raises(ConsentError, match="not in ACTIVE state"):
        await _service(consent)._require_data_processing_consent(consent.id, case)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_evidence_intake_rejects_cross_subject_consent() -> None:
    consent = SimpleNamespace(
        id=uuid.uuid4(),
        subject_id=uuid.uuid4(),
        purpose="data_processing",
        notice_version="1.0",
        state="ACTIVE",
    )
    case = SimpleNamespace(synthetic_subject_id=uuid.uuid4())

    with pytest.raises(ConsentError, match="subject does not match"):
        await _service(consent)._require_data_processing_consent(consent.id, case)
