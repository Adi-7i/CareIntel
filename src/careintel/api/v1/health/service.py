"""
Health check service — readiness probe logic.

Separated from the router so probe logic is independently testable.
The service does NOT raise on failure; it returns a structured result
that the router converts to the appropriate HTTP status.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncEngine

from careintel.core.database import check_database_liveness
from careintel.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Immutable result of a health/readiness check."""

    ready: bool
    checks: dict[str, str] = field(default_factory=dict)
    latency_ms: float = 0.0


async def check_readiness(engine: AsyncEngine) -> HealthStatus:
    """
    Run all readiness probes and aggregate results.

    Currently checks:
    - Database connectivity (SELECT 1)

    Returns a HealthStatus regardless of outcome — never raises.
    Probe failures set ready=False; the router handles the HTTP 503.
    """
    start = time.perf_counter()
    checks: dict[str, str] = {}

    db_ok = await check_database_liveness(engine)
    checks["database"] = "ok" if db_ok else "unavailable"

    elapsed_ms = (time.perf_counter() - start) * 1000
    ready = db_ok

    logger.info(
        "Readiness check completed",
        extra={
            "ready": ready,
            "latency_ms": round(elapsed_ms, 2),
            "checks": checks,
        },
    )

    return HealthStatus(ready=ready, checks=checks, latency_ms=round(elapsed_ms, 2))
