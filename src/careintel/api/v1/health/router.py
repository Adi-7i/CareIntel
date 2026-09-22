"""
Health check endpoints.

GET /api/v1/health/live   — liveness probe (is the process alive?)
GET /api/v1/health/ready  — readiness probe (can the process serve traffic?)

Design decisions:
- /live never touches the database. It must always return 200 if the process
  is running. Used by container orchestrators to decide whether to restart.
- /ready checks downstream dependencies (database). Returns 503 when not ready.
  Used by load balancers to decide whether to route traffic.
- No auth required on health endpoints (standard practice; these are infra probes).
- No PII or sensitive data is included in health responses.
- Route handlers contain no logic beyond request-to-service mapping.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from careintel.api.v1.health.service import check_readiness

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/live",
    summary="Liveness probe",
    description=(
        "Returns 200 if the application process is running. "
        "Does not check downstream dependencies. "
        "Used by container orchestrators to decide whether to restart the process."
    ),
    response_description="Process is alive",
    status_code=status.HTTP_200_OK,
)
async def liveness() -> JSONResponse:
    """Liveness probe — always 200 if the process is handling requests."""
    return JSONResponse(content={"status": "ok"})


@router.get(
    "/ready",
    summary="Readiness probe",
    description=(
        "Returns 200 when the application is ready to serve traffic. "
        "Checks all required downstream dependencies (database, etc). "
        "Returns 503 when any dependency is unavailable."
    ),
    response_description="Readiness status with per-dependency check results",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "One or more dependencies are unavailable"
        }
    },
)
async def readiness(request: Request) -> JSONResponse:
    """Readiness probe — checks database and other dependencies."""
    engine = request.app.state.db_engine
    blob_provider = request.app.state.blob_provider
    health = await check_readiness(engine, blob_provider)

    response_body = {
        "status": "ready" if health.ready else "not_ready",
        "checks": health.checks,
        "latency_ms": health.latency_ms,
    }
    http_status = status.HTTP_200_OK if health.ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=response_body, status_code=http_status)
