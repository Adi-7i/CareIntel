"""
Integration tests for the Structuring API.
"""

import uuid

import pytest
from httpx import AsyncClient

from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer TEST_TOKEN"}


@pytest.fixture
def current_user() -> UserContext:
    return UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"structurer"},
        permissions={Permission.STRUCTURING_WRITE},
        role_facilities={},
    )


async def test_evaluate_case_unauthorized(
    client: AsyncClient,
) -> None:
    """Test evaluating a case without authentication/authorization."""
    case_id = uuid.uuid4()
    run_id = uuid.uuid4()

    response = await client.post(
        f"/api/v1/cases/{case_id}/evaluate",
        json={"extraction_run_id": str(run_id)},
    )
    assert response.status_code == 401


# Since testing the full flow requires mocked auth, consent, and case fixtures,
# and this is a skeleton prototype for Phase 6, we will focus on asserting that
# the route exists and is protected.


async def test_get_timeline_protected(
    client: AsyncClient,
) -> None:
    case_id = uuid.uuid4()
    response = await client.get(f"/api/v1/cases/{case_id}/timeline")
    assert response.status_code == 401
