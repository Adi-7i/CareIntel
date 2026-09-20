"""
Tests for case APIs and CaseService.
"""

import datetime
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from careintel.application.case.case_service import CaseService
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.models import CaseAggregate
from careintel.domain.case.states import CaseState


# Test setup for API with mocked dependencies
@pytest.fixture
def mock_case_service() -> AsyncMock:
    return AsyncMock(spec=CaseService)


@pytest.fixture
def test_user() -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"doctor"},
        permissions={Permission.CASE_READ.value, Permission.CASE_WRITE.value},
    )


@pytest.fixture
def app_with_mocks(app: FastAPI, mock_case_service: AsyncMock, test_user: UserContext) -> FastAPI:
    from careintel.api.deps import get_case_service, get_current_user

    # Mock CurrentUser
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Mock CaseService
    app.dependency_overrides[get_case_service] = lambda: mock_case_service

    return app


@pytest_asyncio.fixture
async def api_client(app_with_mocks: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.api
async def test_create_case_endpoint(
    api_client: AsyncClient, mock_case_service: AsyncMock, test_user: UserContext
) -> None:
    subject_id = uuid.uuid4()
    case_id = uuid.uuid4()

    # Setup mock return
    mock_case_service.create_case.return_value = CaseAggregate(
        case_id=case_id,
        synthetic_subject_id=subject_id,
        facility_id=None,
        state=CaseState.CREATED,
        version=1,
        opened_by=test_user.id,
        assigned_to=None,
        created_at=datetime.datetime.now(datetime.UTC),
        updated_at=datetime.datetime.now(datetime.UTC),
    )

    import unittest.mock

    with unittest.mock.patch("careintel.api.v1.cases.router.ConsentPolicy.require_active"):
        response = await api_client.post(
            "/api/v1/cases",
            json={
                "synthetic_subject_id": str(subject_id),
                "consent_id": str(uuid.uuid4()),
            },
            headers={"Authorization": "Bearer fake_token"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["case_id"] == str(case_id)
    assert data["state"] == "CREATED"
    assert data["version"] == 1


@pytest.mark.api
async def test_transition_case_endpoint(
    api_client: AsyncClient, mock_case_service: AsyncMock, test_user: UserContext
) -> None:
    case_id = uuid.uuid4()

    # Setup mock return
    mock_case_service.transition_state.return_value = CaseAggregate(
        case_id=case_id,
        synthetic_subject_id=uuid.uuid4(),
        facility_id=None,
        state=CaseState.CONSENTED,
        version=2,
        opened_by=test_user.id,
        assigned_to=None,
        created_at=datetime.datetime.now(datetime.UTC),
        updated_at=datetime.datetime.now(datetime.UTC),
    )

    response = await api_client.post(
        f"/api/v1/cases/{case_id}/transitions",
        json={"to_state": "CONSENTED", "expected_version": 1, "reason": "Consent obtained"},
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "CONSENTED"
    assert data["version"] == 2
