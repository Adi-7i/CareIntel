"""Authorization invariants for acknowledgement and completion."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from careintel.application.handoff.handoff_service import HandoffService
from careintel.core.errors import AuthorizationError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.handoff.states import HandoffStatus
from careintel.persistence.models.handoff import HandoffORM


def _actor(actor_id: uuid.UUID, facility_id: uuid.UUID, permissions: set[str]) -> UserContext:
    return UserContext(
        id=actor_id,
        is_active=True,
        roles={"synthetic-role"},
        permissions=permissions,
        role_facilities={"synthetic-role": facility_id},
    )


@pytest.mark.unit
def test_unrelated_handoff_writer_cannot_record_recipient_acknowledgement() -> None:
    facility_id = uuid.uuid4()
    handoff = HandoffORM(sent_by=uuid.uuid4())
    unrelated = _actor(uuid.uuid4(), facility_id, {Permission.HANDOFF_WRITE.value})

    with pytest.raises(AuthorizationError):
        HandoffService._require_acknowledgement_recorder(handoff, unrelated, facility_id)


@pytest.mark.unit
def test_sender_or_recipient_manager_can_record_acknowledgement() -> None:
    facility_id = uuid.uuid4()
    sender_id = uuid.uuid4()
    handoff = HandoffORM(sent_by=sender_id)
    sender = _actor(sender_id, facility_id, {Permission.HANDOFF_WRITE.value})
    manager = _actor(
        uuid.uuid4(),
        facility_id,
        {Permission.HANDOFF_WRITE.value, Permission.RECIPIENT_MANAGE.value},
    )

    HandoffService._require_acknowledgement_recorder(handoff, sender, facility_id)
    HandoffService._require_acknowledgement_recorder(handoff, manager, facility_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_failed_delivery_remains_explicit_and_can_reenter_bounded_retry() -> None:
    handoff = HandoffORM(
        id=uuid.uuid4(),
        status=HandoffStatus.SENDING.value,
        version=2,
        attempt_count=0,
        sent_by=uuid.uuid4(),
    )
    handoff_repo = AsyncMock()
    handoff_repo.get_handoff_for_update.return_value = handoff
    audit_repo = AsyncMock()
    service = HandoffService(
        handoff_repo,
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        audit_repo,
    )

    failed = await service.record_delivery_result(
        handoff.id,
        False,
        None,
        "SyntheticProviderUnavailable",
        "synthetic-correlation",
    )

    assert failed.status == HandoffStatus.DELIVERY_FAILED.value
    assert failed.attempt_count == 1
    assert failed.delivery_reference is None
    retrying = await service.begin_delivery(handoff.id)
    assert retrying.status == HandoffStatus.SENDING.value
    assert retrying.version == 4
    audit_repo.append.assert_awaited_once()
