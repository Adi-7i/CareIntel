"""Encounter authorization, consent, persistence, and audit tests."""

import datetime
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from careintel.application.case.encounter_service import EncounterService
from careintel.core.errors import AuthorizationError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.commands import CreateEncounterCommand


def _actor(facility_id: uuid.UUID) -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"reviewer"},
        permissions={Permission.CASE_READ.value, Permission.CASE_WRITE.value},
        role_facilities={"reviewer": facility_id},
    )


@pytest.mark.asyncio
async def test_encounter_create_is_consent_gated_and_persisted() -> None:
    facility_id = uuid.uuid4()
    case_id = uuid.uuid4()
    actor = _actor(facility_id)
    case_repo = AsyncMock()
    encounter_repo = AsyncMock()
    consent = AsyncMock()
    audit = AsyncMock()
    case_repo.get_by_id.return_value = SimpleNamespace(
        id=case_id,
        facility_id=facility_id,
        synthetic_subject_id=uuid.uuid4(),
    )
    encounter_repo.create.side_effect = lambda item: item
    service = EncounterService(case_repo, encounter_repo, consent, audit)
    command = CreateEncounterCommand(
        case_id=case_id,
        encounter_type="synthetic_visit",
        occurred_at=datetime.datetime.now(datetime.UTC),
        notes=None,
        actor_id=actor.id,
        correlation_id="synthetic-correlation",
    )

    result = await service.create(command, actor)

    assert result.case_id == case_id
    persisted = encounter_repo.create.await_args.args[0]
    assert persisted.occurred_at.tzinfo is None
    consent.require_active.assert_awaited_once()
    encounter_repo.create.assert_awaited_once()
    audit.append.assert_awaited_once()


@pytest.mark.asyncio
async def test_encounter_cross_facility_create_is_denied_before_consent() -> None:
    case_repo = AsyncMock()
    consent = AsyncMock()
    case_repo.get_by_id.return_value = SimpleNamespace(
        id=uuid.uuid4(),
        facility_id=uuid.uuid4(),
        synthetic_subject_id=uuid.uuid4(),
    )
    service = EncounterService(case_repo, AsyncMock(), consent, AsyncMock())
    actor = _actor(uuid.uuid4())
    command = CreateEncounterCommand(
        case_id=uuid.uuid4(),
        encounter_type="synthetic_visit",
        occurred_at=datetime.datetime.now(datetime.UTC),
        notes=None,
        actor_id=actor.id,
        correlation_id="synthetic-correlation",
    )

    with pytest.raises(AuthorizationError):
        await service.create(command, actor)

    consent.require_active.assert_not_awaited()
