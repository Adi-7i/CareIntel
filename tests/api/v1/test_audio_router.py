"""Tests for the Audio API router."""

import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from careintel.api.deps import get_current_user, get_speech_service
from careintel.application.audio.speech_service import SpeechService
from careintel.domain.auth.models import UserContext
from careintel.infrastructure.tts.demo_provider import DemoTTSProvider
from careintel.persistence.repositories.audit_repo import AuditRepository


@pytest.fixture
def mock_audit_repo():
    mock = AsyncMock(spec=AuditRepository)
    return mock


@pytest.fixture
def mock_speech_service(mock_audit_repo):
    provider = DemoTTSProvider()
    return SpeechService(tts_provider=provider, audit_repo=mock_audit_repo)


@pytest.fixture
def override_auth(app):
    test_user = UserContext(id=uuid.uuid4(), is_active=True, roles={"physician"})
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield test_user
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_synthesize_speech_success(
    client: AsyncClient,
    app,
    override_auth,
    mock_speech_service,
) -> None:
    """Test successful speech synthesis using the demo provider."""
    app.dependency_overrides[get_speech_service] = lambda: mock_speech_service
    response = await client.post(
        "/api/v1/audio/speech",
        json={"text": "Hello world", "voice": "nova"},
        headers={"Authorization": "Bearer dummy"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 0
    assert response.content.startswith(b"RIFF")


@pytest.mark.asyncio
async def test_synthesize_speech_unauthorized(
    client: AsyncClient,
) -> None:
    """Test that unauthorized users cannot synthesize speech."""
    response = await client.post(
        "/api/v1/audio/speech",
        json={"text": "Hello world"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_synthesize_speech_text_too_long(
    client: AsyncClient,
    app,
    override_auth,
    mock_speech_service,
) -> None:
    """Test validation of maximum text length."""
    app.dependency_overrides[get_speech_service] = lambda: mock_speech_service
    long_text = "A" * 4097
    response = await client.post(
        "/api/v1/audio/speech",
        json={"text": long_text},
        headers={"Authorization": "Bearer dummy"}
    )

    assert response.status_code == 422
