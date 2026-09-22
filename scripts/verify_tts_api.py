"""Verify the real TTS HTTP-to-Azure path with synthetic content."""

from __future__ import annotations

import asyncio
import uuid

import httpx
from asgi_lifespan import LifespanManager

from careintel.api.deps import get_current_user
from careintel.domain.auth.models import UserContext
from careintel.main import create_app


async def main() -> None:
    app = create_app()
    synthetic_actor = UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"synthetic_verifier"},
        permissions=set(),
        role_facilities={},
    )

    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            unauthorized = await client.post(
                "/api/v1/audio/speech", json={"text": "Synthetic verification."}
            )
            app.dependency_overrides[get_current_user] = lambda: synthetic_actor
            try:
                started = asyncio.get_running_loop().time()
                response = await client.post(
                    "/api/v1/audio/speech",
                    json={"text": "CareIntel synthetic speech verification.", "voice": "nova"},
                )
                latency_ms = (asyncio.get_running_loop().time() - started) * 1000
            finally:
                app.dependency_overrides.clear()

    checks = {
        "missing_jwt_rejected": unauthorized.status_code == 401,
        "authorized_route_success": response.status_code == 200,
        "binary_audio_nonempty": bool(response.content),
        "audio_content_type": response.headers.get("content-type", "").startswith("audio/"),
    }
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"latency_ms: {latency_ms:.2f}")
    print("auth_scope: missing-JWT enforced; successful path uses a synthetic dependency override")
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    asyncio.run(main())
