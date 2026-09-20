"""
Consent unit tests.
"""

from __future__ import annotations

import uuid

import pytest

from careintel.core.errors import ConsentError
from careintel.domain.consent.models import ConsentContext
from careintel.domain.consent.policy import ConsentPolicy
from careintel.domain.consent.purpose import ConsentPurpose


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
