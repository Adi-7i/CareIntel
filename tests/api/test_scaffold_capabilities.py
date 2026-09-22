"""Incomplete public capabilities must never return success-shaped placeholders."""

import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from careintel.domain.auth.models import UserContext


@pytest.fixture
def authenticated_app(app: FastAPI) -> FastAPI:
    from careintel.api.deps import get_current_user

    async def user() -> UserContext:
        return UserContext(id=uuid.uuid4(), is_active=True)

    app.dependency_overrides[get_current_user] = user
    return app


@pytest.mark.api
@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("GET", "/api/v1/queue", None),
        (
            "POST",
            f"/api/v1/cases/{uuid.uuid4()}/escalation",
            {"reason": "synthetic", "expected_version": 1},
        ),
        ("POST", f"/api/v1/handoffs/{uuid.uuid4()}/complete", None),
        ("GET", f"/api/v1/cases/{uuid.uuid4()}/timeline", None),
    ],
)
async def test_incomplete_capability_returns_501(
    client: AsyncClient,
    authenticated_app: FastAPI,
    method: str,
    path: str,
    json: dict[str, Any] | None,
) -> None:
    response = await client.request(method, path, json=json)

    assert response.status_code == 501
    assert response.json()["error"]["code"] == "CAPABILITY_NOT_IMPLEMENTED"
