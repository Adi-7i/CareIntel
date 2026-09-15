"""API-level tests for the global error contract."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestErrorContract:
    """Tests that error responses conform to the standard envelope."""

    async def test_404_returns_error_envelope(self, client: AsyncClient) -> None:
        """Unknown endpoints return a structured error envelope, not raw FastAPI 404."""
        response = await client.get("/api/v1/nonexistent/endpoint")
        assert response.status_code == 404
        data = response.json()
        # Must have 'error' envelope
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "correlation_id" in data["error"]

    async def test_404_error_code_is_not_found(self, client: AsyncClient) -> None:
        """404 responses use NOT_FOUND error code."""
        response = await client.get("/api/v1/totally/unknown/path")
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"

    async def test_error_correlation_id_matches_header(self, client: AsyncClient) -> None:
        """Error body correlation_id matches the X-Correlation-ID response header."""
        response = await client.get("/api/v1/nonexistent")
        data = response.json()
        header_id = response.headers.get("x-correlation-id")
        body_id = data["error"]["correlation_id"]
        assert header_id == body_id

    async def test_no_stack_trace_in_error_response(self, client: AsyncClient) -> None:
        """Error responses never include stack traces or internal paths."""
        response = await client.get("/api/v1/nonexistent")
        text = response.text
        assert "Traceback" not in text
        assert 'File "' not in text
        assert "careintel/" not in text

    async def test_method_not_allowed_returns_error_envelope(self, client: AsyncClient) -> None:
        """405 responses also use the error envelope."""
        # POST to a GET-only endpoint
        response = await client.post("/api/v1/health/live")
        assert response.status_code == 405
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
