"""Tests for the Speech Service."""

import uuid
from unittest.mock import AsyncMock

import pytest

from careintel.application.audio.speech_service import SpeechService
from careintel.core.errors import ValidationError
from careintel.domain.auth.models import UserContext
from careintel.infrastructure.tts.demo_provider import DemoTTSProvider
from careintel.persistence.repositories.audit_repo import AuditRepository


@pytest.fixture
def mock_audit_repo():
    return AsyncMock(spec=AuditRepository)


@pytest.fixture
def user_context() -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"physician"},
    )


@pytest.mark.asyncio
async def test_synthesize_speech_success(mock_audit_repo, user_context) -> None:
    provider = DemoTTSProvider()
    service = SpeechService(tts_provider=provider, audit_repo=mock_audit_repo)

    result = await service.synthesize_speech("Test speech", "nova", user_context)

    assert result.audio_format == "wav"
    assert result.voice == "nova"
    assert len(result.audio_bytes) > 0
    assert mock_audit_repo.append.call_count == 1

    audit_event = mock_audit_repo.append.call_args[0][0]
    assert audit_event.event_type == "processing_completed"
    assert audit_event.target_type == "tts"


@pytest.mark.asyncio
async def test_synthesize_speech_empty_text(mock_audit_repo, user_context) -> None:
    provider = DemoTTSProvider()
    service = SpeechService(tts_provider=provider, audit_repo=mock_audit_repo)

    with pytest.raises(ValidationError, match="Text cannot be empty"):
        await service.synthesize_speech("   ", "nova", user_context)

    assert mock_audit_repo.append.call_count == 0


@pytest.mark.asyncio
async def test_synthesize_speech_too_long(mock_audit_repo, user_context) -> None:
    provider = DemoTTSProvider()
    service = SpeechService(tts_provider=provider, audit_repo=mock_audit_repo)

    with pytest.raises(ValidationError, match="Text length exceeds maximum"):
        await service.synthesize_speech("A" * 5000, "nova", user_context)

    assert mock_audit_repo.append.call_count == 0
