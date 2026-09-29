"""
Health check service — readiness probe logic.

Separated from the router so probe logic is independently testable.
The service does NOT raise on failure; it returns a structured result
that the router converts to the appropriate HTTP status.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable
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

    async def _bounded_probe(name: str, probe: Awaitable[bool]) -> bool:
        task = asyncio.ensure_future(probe)
        done, _pending = await asyncio.wait(
            {task},
            timeout=settings.readiness_timeout_seconds,
        )
        if not done:
            task.cancel()
            task.add_done_callback(
                lambda completed: None if completed.cancelled() else completed.exception()
            )
            logger.warning(
                "Dependency readiness check timed out",
                extra={"dependency": name},
            )
            return False
        try:
            return bool(task.result())
        except Exception as exc:
            logger.warning(
                "Dependency readiness check failed",
                extra={"dependency": name, "error_type": type(exc).__name__},
            )
            return False

    redis_url = settings.redis_url.get_secret_value() if settings.redis_url else None

    async def _redis_probe() -> bool:
        if not redis_url:
            return not settings.is_production
        r = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=settings.readiness_timeout_seconds,
            socket_timeout=settings.readiness_timeout_seconds,
        )
        try:
            result = bool(await r.ping())
        except asyncio.CancelledError:
            raise
        except Exception:
            try:
                await asyncio.wait_for(
                    r.aclose(),
                    timeout=settings.readiness_timeout_seconds,
                )
            except Exception as exc:
                logger.warning(
                    "Redis health client close failed",
                    extra={"error_type": type(exc).__name__},
                )
            raise
        else:
            await asyncio.wait_for(
                r.aclose(),
                timeout=settings.readiness_timeout_seconds,
            )
            return result

    # Touch storage without downloading content. A missing dummy object is a
    # successful connectivity result; only provider exceptions fail readiness.
    async def _blob_probe() -> bool:
        await blob_provider.exists("healthcheck_dummy_key_do_not_create")
        return True

    db_ok, redis_ok, blob_ok = await asyncio.gather(
        _bounded_probe("database", check_database_liveness(engine)),
        _bounded_probe("redis", _redis_probe()),
        _bounded_probe("blob_storage", _blob_probe()),
    )

    checks["database"] = "ok" if db_ok else "unavailable"
    checks["redis"] = "ok" if redis_ok else "unavailable"
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
