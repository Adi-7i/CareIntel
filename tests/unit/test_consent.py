"""
Consent unit tests.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from careintel.core.errors import ConsentError
from careintel.domain.consent.models import ConsentContext
from careintel.domain.consent.policy import ConsentPolicy
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.persistence.models.consent import ConsentEventORM, ConsentORM
from careintel.persistence.repositories.consent_repo import ConsentRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consent_repository_flushes_parent_before_initial_event() -> None:
    session = MagicMock()
    session.flush = AsyncMock()
    consent = ConsentORM(
        id=uuid.uuid4(),
        subject_id=uuid.uuid4(),
        purpose=ConsentPurpose.DATA_PROCESSING.value,
        notice_version="1.0",
        state="REQUESTED",
    )
    event = ConsentEventORM(consent_id=consent.id, event_type="REQUESTED")

    await ConsentRepository(session).create(consent, event)

    assert session.method_calls == [
        call.add(consent),
        call.flush([consent]),
        call.add(event),
        call.flush([event]),
    ]


@pytest.mark.unit
def test_consent_policy_require_active_valid() -> None:
    subject_id = uuid.uuid4()
    ctx = ConsentContext(
        id=uuid.uuid4(),
        subject_id=subject_id,
        purpose=ConsentPurpose.DATA_PROCESSING.value,
        notice_version="1.0",
        state="ACTIVE",
    )
    # Should not raise
    validated = ConsentPolicy.require_active(
        consent=ctx,
        subject_id=subject_id,
        purpose=ConsentPurpose.DATA_PROCESSING,
        required_notice_version="1.0",
    )
    assert validated == ctx


@pytest.mark.unit
def test_consent_policy_require_active_missing() -> None:
    with pytest.raises(ConsentError, match="No active consent found"):
        ConsentPolicy.require_active(
            consent=None,
            subject_id=uuid.uuid4(),
            purpose=ConsentPurpose.DATA_PROCESSING,
            required_notice_version="1.0",
        )


@pytest.mark.unit
def test_consent_policy_require_active_wrong_subject() -> None:
    ctx = ConsentContext(
        id=uuid.uuid4(),
        subject_id=uuid.uuid4(),
        purpose=ConsentPurpose.DATA_PROCESSING.value,
        notice_version="1.0",
        state="ACTIVE",
    )
    with pytest.raises(ConsentError, match="Consent subject does not match"):
        ConsentPolicy.require_active(
            consent=ctx,
            subject_id=uuid.uuid4(),
            purpose=ConsentPurpose.DATA_PROCESSING,
            required_notice_version="1.0",
        )


@pytest.mark.unit
def test_consent_policy_require_active_stale_version() -> None:
    subject_id = uuid.uuid4()
    ctx = ConsentContext(
        id=uuid.uuid4(),
        subject_id=subject_id,
        purpose=ConsentPurpose.DATA_PROCESSING.value,
        notice_version="1.0",
        state="ACTIVE",
    )
    with pytest.raises(ConsentError, match="mismatch or stale"):
        ConsentPolicy.require_active(
            consent=ctx,
            subject_id=subject_id,
            purpose=ConsentPurpose.DATA_PROCESSING,
            required_notice_version="2.0",
        )


@pytest.mark.unit
def test_consent_policy_require_active_not_active() -> None:
    subject_id = uuid.uuid4()
    ctx = ConsentContext(
        id=uuid.uuid4(),
        subject_id=subject_id,
        purpose=ConsentPurpose.DATA_PROCESSING.value,
        notice_version="1.0",
        state="WITHDRAWN",
    )
    with pytest.raises(ConsentError, match="not in ACTIVE state"):
        ConsentPolicy.require_active(
            consent=ctx,
            subject_id=subject_id,
            purpose=ConsentPurpose.DATA_PROCESSING,
            required_notice_version="1.0",
        )
