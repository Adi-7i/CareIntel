"""Recovered human-workflow endpoints expose real, guarded API contracts."""

import uuid

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
def test_recovered_human_workflow_routes_are_registered(authenticated_app: FastAPI) -> None:
    paths = authenticated_app.openapi()["paths"]

    assert "get" in paths["/api/v1/queue"]
    assert "post" in paths["/api/v1/cases/{case_id}/escalation"]
    assert "post" in paths["/api/v1/handoffs/{handoff_id}/complete"]


@pytest.mark.api
async def test_review_queue_requires_server_side_permission(
    client: AsyncClient, authenticated_app: FastAPI
) -> None:
    response = await client.get("/api/v1/queue")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTHORIZATION_DENIED"


@pytest.mark.api
@pytest.mark.parametrize(
    ("path", "body"),
    [
        (f"/api/v1/cases/{uuid.uuid4()}/escalation", {"reason": "synthetic"}),
        (f"/api/v1/handoffs/{uuid.uuid4()}/complete", None),
    ],
)
async def test_human_workflow_commands_require_concurrency_versions(
    client: AsyncClient,
    authenticated_app: FastAPI,
    path: str,
    body: dict[str, str] | None,
) -> None:
    response = await client.post(path, json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
