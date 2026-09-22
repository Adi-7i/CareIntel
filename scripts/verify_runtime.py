"""Secret-safe FastAPI startup, contract, health, and latency verification."""

from __future__ import annotations

import asyncio
import statistics
import time
from collections import Counter
from collections.abc import Iterable
from typing import Any

import httpx
from asgi_lifespan import LifespanManager

from careintel.main import create_app


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def _route_keys(routes: Iterable[Any], prefix: str = "") -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    for route in routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if isinstance(methods, set) and isinstance(path, str):
            keys.extend((method, f"{prefix}{path}") for method in methods)
        original_router = getattr(route, "original_router", None)
        nested = getattr(original_router, "routes", None)
        include_context = getattr(route, "include_context", None)
        nested_prefix = getattr(include_context, "prefix", prefix)
        if not isinstance(nested_prefix, str):
            nested_prefix = prefix
        if isinstance(nested, Iterable):
            keys.extend(_route_keys(nested, nested_prefix))
    return keys


async def main() -> None:
    app = create_app()
    route_keys = _route_keys(app.routes)
    duplicates = [key for key, count in Counter(route_keys).items() if count > 1]

    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            live = await client.get("/api/v1/health/live")
            ready = await client.get("/api/v1/health/ready")
            synthetic_case = {
                "synthetic_subject_id": "00000000-0000-0000-0000-000000000101",
                "facility_id": "00000000-0000-0000-0000-000000000102",
                "consent_id": "00000000-0000-0000-0000-000000000103",
            }
            missing_jwt = await client.post("/api/v1/cases", json=synthetic_case)
            malformed_jwt = await client.post(
                "/api/v1/cases",
                json=synthetic_case,
                headers={"Authorization": "Bearer malformed.synthetic.token"},
            )
            openapi = await client.get("/api/openapi.json")

            samples: list[float] = []
            for _ in range(100):
                started = time.perf_counter()
                response = await client.get("/api/v1/health/live")
                samples.append((time.perf_counter() - started) * 1000)
                if response.status_code != 200:
                    raise RuntimeError("Liveness sample failed")

    openapi_payload = openapi.json() if openapi.status_code == 200 else {}
    openapi_paths = openapi_payload.get("paths", {})
    checks = {
        "lifespan_startup_shutdown": True,
        "liveness_200": live.status_code == 200,
        "readiness_200": ready.status_code == 200,
        "readiness_dependencies": ready.json().get("checks")
        == {"database": "ok", "redis": "ok", "blob_storage": "ok"},
        "missing_jwt_rejected": missing_jwt.status_code == 401,
        "malformed_jwt_rejected": malformed_jwt.status_code == 401,
        "openapi_200": openapi.status_code == 200 and bool(openapi_paths),
        "duplicate_method_paths_absent": not duplicates,
        "debug_routes_absent": not any("debug" in path.lower() for _, path in route_keys),
    }
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"registered_api_routes: {len(route_keys)}")
    print(f"openapi_paths: {len(openapi_paths)}")
    print("liveness_samples: 100")
    print(f"liveness_mean_ms: {statistics.fmean(samples):.3f}")
    print(f"liveness_p50_ms: {_percentile(samples, 0.50):.3f}")
    print(f"liveness_p95_ms: {_percentile(samples, 0.95):.3f}")
    print(f"liveness_p99_ms: {_percentile(samples, 0.99):.3f}")
    print(f"readiness_latency_ms: {ready.json().get('latency_ms', 'unavailable')}")
    print("latency_scope: in-process ASGI; liveness only; not a load test")
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    asyncio.run(main())
