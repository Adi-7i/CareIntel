"""API-level tests for health endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestLivenessEndpoint:
    """Tests for GET /api/v1/health/live."""

    async def test_liveness_returns_200(self, client: AsyncClient) -> None:
        """Liveness probe always returns 200."""
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200

    async def test_liveness_returns_ok_status(self, client: AsyncClient) -> None:
        """Liveness response body contains status: ok."""
        response = await client.get("/api/v1/health/live")
        data = response.json()
        assert data["status"] == "ok"

    async def test_liveness_has_correlation_id_header(self, client: AsyncClient) -> None:
        """Liveness response includes X-Correlation-ID header."""
        response = await client.get("/api/v1/health/live")
        assert "x-correlation-id" in response.headers

    async def test_liveness_echoes_supplied_correlation_id(self, client: AsyncClient) -> None:
        """Liveness echoes back the correlation ID from the request."""
        supplied_id = "test-correlation-id-abc123"
        response = await client.get(
            "/api/v1/health/live",
            headers={"X-Correlation-ID": supplied_id},
        )
        assert response.headers.get("x-correlation-id") == supplied_id


@pytest.mark.api
class TestReadinessEndpoint:
    """Tests for GET /api/v1/health/ready."""

    async def test_readiness_returns_200_when_db_ok(self, client: AsyncClient) -> None:
        """Readiness probe returns 200 when database is reachable."""
        with patch(
            "careintel.api.v1.health.service.check_database_liveness",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = await client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "ok"

    async def test_readiness_returns_503_when_db_unavailable(self, client: AsyncClient) -> None:
        """Readiness probe returns 503 when database is unreachable."""
        with patch(
            "careintel.api.v1.health.service.check_database_liveness",
            new_callable=AsyncMock,
            return_value=False,
        ):
            response = await client.get("/api/v1/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["database"] == "unavailable"

    async def test_readiness_includes_latency_ms(self, client: AsyncClient) -> None:
        """Readiness response includes latency_ms for observability."""
        with patch(
            "careintel.api.v1.health.service.check_database_liveness",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = await client.get("/api/v1/health/ready")
        data = response.json()
        assert "latency_ms" in data
        assert isinstance(data["latency_ms"], float | int)

    async def test_readiness_has_correlation_id_header(self, client: AsyncClient) -> None:
        """Readiness response includes X-Correlation-ID header."""
        with patch(
            "careintel.api.v1.health.service.check_database_liveness",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = await client.get("/api/v1/health/ready")
        assert "x-correlation-id" in response.headers
