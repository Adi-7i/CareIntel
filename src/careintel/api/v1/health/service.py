"""
Health check service — readiness probe logic.

Separated from the router so probe logic is independently testable.
The service does NOT raise on failure; it returns a structured result
that the router converts to the appropriate HTTP status.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncEngine

from careintel.core.config import get_settings
from careintel.core.database import check_database_liveness
from careintel.core.logging import get_logger
from careintel.infrastructure.storage.port import BlobStoragePort

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Immutable result of a health/readiness check."""

    ready: bool
    checks: dict[str, str] = field(default_factory=dict)
    latency_ms: float = 0.0


async def check_readiness(engine: AsyncEngine, blob_provider: BlobStoragePort) -> HealthStatus:
    """
    Run all readiness probes and aggregate results.

    Currently checks:
    - Database connectivity (SELECT 1)
    - Redis connectivity (PING)
    - Blob Storage (existence check of a dummy key)

    Returns a HealthStatus regardless of outcome — never raises.
    Probe failures set ready=False; the router handles the HTTP 503.
    """
    start = time.perf_counter()
    checks: dict[str, str] = {}
    settings = get_settings()

    db_ok = await check_database_liveness(engine)
    checks["database"] = "ok" if db_ok else "unavailable"

    redis_ok = False
    redis_url = settings.redis_url.get_secret_value() if settings.redis_url else None
    if redis_url:
        try:
            r = redis.Redis.from_url(redis_url)
            await r.ping()
            redis_ok = True
            await r.aclose()
        except Exception as exc:
            logger.warning(
                "Redis health check failed",
                extra={"error_type": type(exc).__name__},
            )
    else:
        # If running locally without redis, we consider it ok (demo mode)
        # In production, settings validation would have failed startup if redis_url was missing.
        redis_ok = not settings.is_production

    checks["redis"] = "ok" if redis_ok else "unavailable"

    blob_ok = False
    try:
        # Touch storage without downloading content.
        await blob_provider.exists("healthcheck_dummy_key_do_not_create")
        blob_ok = True
    except Exception as exc:
        logger.warning(
            "Blob storage health check failed",
            extra={"error_type": type(exc).__name__},
        )

    checks["blob_storage"] = "ok" if blob_ok else "unavailable"

    elapsed_ms = (time.perf_counter() - start) * 1000
    ready = db_ok and redis_ok and blob_ok

    logger.info(
        "Readiness check completed",
        extra={
            "ready": ready,
            "latency_ms": round(elapsed_ms, 2),
            "checks": checks,
        },
    )

    return HealthStatus(ready=ready, checks=checks, latency_ms=round(elapsed_ms, 2))
