import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from careintel.application.processing.access import ProcessingAccessGuard
from careintel.core.errors import AuthorizationError
from careintel.domain.auth.models import UserContext
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.domain.evidence.states import EvidenceState


@pytest.mark.asyncio
async def test_read_access_allows_terminal_evidence_without_write_permission() -> None:
    evidence_id = uuid.uuid4()
    case_id = uuid.uuid4()
    facility_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    evidence = SimpleNamespace(
        id=evidence_id,
        case_id=case_id,
        state=EvidenceState.FAILED.value,
    )
    case = SimpleNamespace(
        id=case_id,
        facility_id=facility_id,
        synthetic_subject_id=subject_id,
    )
    evidence_repo = AsyncMock()
    evidence_repo.get_by_id.return_value = evidence
    case_repo = AsyncMock()
    case_repo.get_by_id.return_value = case
    consent_service = AsyncMock()
    actor = UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"reviewer"},
        permissions={"processing:read"},
        role_facilities={"reviewer": facility_id},
    )
    guard = ProcessingAccessGuard(evidence_repo, case_repo, consent_service)

    assert await guard.require_readable_evidence(evidence_id, actor) is evidence
    consent_service.require_active.assert_awaited_once_with(
        subject_id,
        ConsentPurpose.DATA_PROCESSING.value,
        "1.0",
    )

    with pytest.raises(AuthorizationError):
        await guard.require_ready_evidence(evidence_id, actor)
