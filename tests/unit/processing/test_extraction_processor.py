"""
Unit tests for ExtractionProcessor.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from careintel.application.processing.extraction_processor import ExtractionProcessor
from careintel.core.config import Settings
from careintel.domain.auth.models import UserContext
from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.evidence.states import EvidenceState
from careintel.domain.processing.processing_models import CandidateField, ExtractionProvenance
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.infrastructure.extraction.port import ExtractionResult
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
        "extraction_provider": AsyncMock(),
    }


@pytest.fixture
def processor(mocks: dict[str, AsyncMock]) -> ExtractionProcessor:
    settings = Settings(
        database_url=SecretStr("mock"),
        secret_key=SecretStr("mock"),
        jwt_secret_key=SecretStr("mock"),
        extraction_provider="demo",
    )
    return ExtractionProcessor(
        settings=settings,
        evidence_repo=mocks["evidence_repo"],
        processing_repo=mocks["processing_repo"],
        outbox_repo=mocks["outbox_repo"],
        extraction_provider=mocks["extraction_provider"],
    )


@pytest.mark.asyncio
async def test_process_success(
    processor: ExtractionProcessor,
    mocks: dict[str, AsyncMock],
    evidence: EvidenceORM,
    user: UserContext,
) -> None:
    mocks["evidence_repo"].get_by_id.return_value = evidence
    mocks["processing_repo"].get_run_by_idempotency_key.return_value = None

    cand = CandidateField(
        candidate_id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        field_type="symptom",
        value="fever",
        provenance=[ExtractionProvenance(evidence_id=evidence.id)],
    )

    mocks["extraction_provider"].extract_candidates.return_value = ExtractionResult(
        candidates=[cand], provider_version="v1"
    )

    await processor.process(evidence.id, "patient has a fever", user, "corr")

    mocks["processing_repo"].add_run.assert_called_once()
    added_run = mocks["processing_repo"].add_run.call_args[0][0]
    assert added_run.status == ProcessingStatus.COMPLETED.value
