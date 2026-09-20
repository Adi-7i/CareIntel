"""
Tests for Evidence APIs.
"""

import datetime
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from careintel.application.evidence.evidence_service import EvidenceService
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.evidence.models import EvidenceAggregate
from careintel.domain.evidence.states import EvidenceState


@pytest.fixture
def mock_evidence_service() -> AsyncMock:
    return AsyncMock(spec=EvidenceService)


@pytest.fixture
def test_user() -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"doctor"},
        permissions={Permission.EVIDENCE_READ.value, Permission.EVIDENCE_WRITE.value},
    )


@pytest.fixture
def app_with_mocks(
    app: FastAPI, mock_evidence_service: AsyncMock, test_user: UserContext
) -> FastAPI:
    from careintel.api.deps import get_current_user, get_evidence_service

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_evidence_service] = lambda: mock_evidence_service

    return app


@pytest_asyncio.fixture
async def api_client(app_with_mocks: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.api
async def test_register_text_endpoint(
    api_client: AsyncClient, mock_evidence_service: AsyncMock, test_user: UserContext
) -> None:
    case_id = uuid.uuid4()
    evidence_id = uuid.uuid4()

    # Setup mock return
    mock_evidence_service.register_text_evidence.return_value = EvidenceAggregate(
        evidence_id=evidence_id,
        case_id=case_id,
        modality=EvidenceModality.TEXT,
        state=EvidenceState.READY,
        content_type="text/plain",
        size_bytes=100,
        created_by=test_user.id,
        created_at=datetime.datetime.now(datetime.UTC),
        provenance={"source": "direct_input"},
    )

    response = await api_client.post(
        "/api/v1/evidence/text",
        json={
            "case_id": str(case_id),
            "text_content": "This is test evidence.",
            "consent_id": str(uuid.uuid4()),
        },
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["evidence_id"] == str(evidence_id)
    assert data["state"] == "READY"
    assert data["modality"] == "text"


@pytest.mark.api
async def test_upload_file_endpoint(
    api_client: AsyncClient, mock_evidence_service: AsyncMock, test_user: UserContext
) -> None:
    case_id = uuid.uuid4()
    evidence_id = uuid.uuid4()

    mock_evidence_service.start_file_upload.return_value = EvidenceAggregate(
        evidence_id=evidence_id,
        case_id=case_id,
        modality=EvidenceModality.DOCUMENT,
        state=EvidenceState.PENDING_UPLOAD,
        content_type="application/pdf",
        size_bytes=0,
        created_by=test_user.id,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    mock_evidence_service.complete_file_upload.return_value = EvidenceAggregate(
        evidence_id=evidence_id,
        case_id=case_id,
        modality=EvidenceModality.DOCUMENT,
        state=EvidenceState.STORED,
        content_type="application/pdf",
        size_bytes=1024,
        created_by=test_user.id,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    files = {"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    data = {
        "case_id": str(case_id),
        "consent_id": str(uuid.uuid4()),
        "modality": "document",
    }

    response = await api_client.post(
        "/api/v1/evidence/files",
        data=data,
        files=files,
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["evidence_id"] == str(evidence_id)
    assert res_data["state"] == "STORED"


@pytest.mark.api
async def test_get_evidence_endpoint(
    api_client: AsyncClient, mock_evidence_service: AsyncMock, test_user: UserContext
) -> None:
    case_id = uuid.uuid4()
    evidence_id = uuid.uuid4()

    mock_evidence_service.get_evidence.return_value = EvidenceAggregate(
        evidence_id=evidence_id,
        case_id=case_id,
        modality=EvidenceModality.IMAGE,
        state=EvidenceState.READY,
        content_type="image/jpeg",
        size_bytes=2048,
        created_by=test_user.id,
        created_at=datetime.datetime.now(datetime.UTC),
    )

    response = await api_client.get(
        f"/api/v1/evidence/{evidence_id}",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["evidence_id"] == str(evidence_id)
    # Ensure sensitive fields aren't present
    assert "storage_key" not in data
    assert "sha256_checksum" not in data


@pytest.mark.api
async def test_generate_sas_url(api_client: AsyncClient, mock_evidence_service: AsyncMock) -> None:
    evidence_id = uuid.uuid4()
    mock_evidence_service.generate_secure_download_url.return_value = (
        "https://example.com/sas?token=123"
    )

    response = await api_client.get(
        f"/api/v1/evidence/{evidence_id}/download",
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["download_url"] == "https://example.com/sas?token=123"
    assert "expires_at" in data
