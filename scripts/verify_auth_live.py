"""Live synthetic login, JWT session, logout, and revocation verification."""

from __future__ import annotations

import asyncio
import secrets
import uuid

import httpx
from asgi_lifespan import LifespanManager
from sqlalchemy import select

from careintel.application.auth.password_hasher import PasswordHasher
from careintel.core.config import get_settings
from careintel.core.database import build_engine, build_session_factory
from careintel.main import create_app
from careintel.persistence.models.user import RoleORM, UserORM, UserRoleORM


async def main() -> None:
    settings = get_settings()
    synthetic_id = uuid.uuid4()
    email = f"release-verifier-{synthetic_id}@example.com"
    password = secrets.token_urlsafe(32)

    seed_engine = build_engine(settings)
    session_factory = build_session_factory(seed_engine)
    try:
        async with session_factory() as session:
            admin_role = (
                await session.execute(select(RoleORM).where(RoleORM.name == "admin"))
            ).scalar_one()
            session.add(
                UserORM(
                    id=synthetic_id,
                    email=email,
                    display_name="Synthetic Release Verifier",
                    password_hash=PasswordHasher().hash(password),
                    is_active=True,
                    is_verified=True,
                )
            )
            session.add(
                UserRoleORM(
                    user_id=synthetic_id,
                    role_id=admin_role.id,
                    facility_id=None,
                )
            )
            await session.commit()
    finally:
        await seed_engine.dispose()

    app = create_app()
    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            wrong_password = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": "incorrect"}
            )
            login = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": password}
            )
            token = login.json().get("access_token", "") if login.status_code == 200 else ""
            auth_header = {"Authorization": f"Bearer {token}"}
            profile = await client.get("/api/v1/auth/me", headers=auth_header)
            logout = await client.post("/api/v1/auth/logout", headers=auth_header)
            replay = await client.get("/api/v1/auth/me", headers=auth_header)

    cleanup_engine = build_engine(settings)
    cleanup_factory = build_session_factory(cleanup_engine)
    try:
        async with cleanup_factory() as session:
            user = await session.get(UserORM, synthetic_id)
            if user is not None:
                user.is_active = False
                await session.commit()
    finally:
        await cleanup_engine.dispose()

    checks = {
        "wrong_password_rejected": wrong_password.status_code == 401,
        "login_issued_token": login.status_code == 200 and bool(token),
        "jwt_profile_loaded": profile.status_code == 200,
        "role_permissions_loaded": profile.status_code == 200
        and "admin" in profile.json().get("roles", []),
        "logout_revoked_session": logout.status_code == 204,
        "revoked_token_replay_rejected": replay.status_code == 401,
        "synthetic_account_deactivated": user is not None and not user.is_active,
    }
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    asyncio.run(main())
