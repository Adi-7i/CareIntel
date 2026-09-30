"""Live PostgreSQL verification for first-admin bootstrap atomicity and login."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from careintel.api.deps import _db_session_provider
from careintel.application.auth.admin_bootstrap_service import (
    AdminBootstrapScope,
    BootstrapAdminCommand,
    FirstAdminBootstrapService,
)
from careintel.application.auth.password_hasher import PasswordHasher
from careintel.core.config import Settings
from careintel.core.database import build_engine
from careintel.core.errors import ConflictError
from careintel.domain.auth.permissions import Permission
from careintel.main import create_app
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.user import (
    RoleORM,
    RolePermissionORM,
    UserORM,
    UserRoleORM,
)
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.user_repo import UserRepository

pytestmark = pytest.mark.integration


def _command(user_id: uuid.UUID, password: str) -> BootstrapAdminCommand:
    return BootstrapAdminCommand(
        user_id=user_id,
        email=f"bootstrap-{user_id}@example.com",
        display_name="Synthetic Bootstrap Administrator",
        password=password,
        scope=AdminBootstrapScope.SYSTEM_WIDE,
    )


async def _test_session(
    settings: Settings,
) -> tuple[object, object, object, AsyncSession]:
    engine = build_engine(settings)
    connection = await engine.connect()
    outer = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    return engine, connection, outer, session_factory()


async def _remove_admin_assignments(session: AsyncSession) -> RoleORM:
    admin_role = (
        await session.execute(select(RoleORM).where(RoleORM.name == "admin"))
    ).scalar_one()
    await session.execute(delete(UserRoleORM).where(UserRoleORM.role_id == admin_role.id))
    await session.flush()
    return admin_role


async def test_first_admin_persists_audit_permissions_and_authenticates_via_login_api(
    settings: Settings,
) -> None:
    if "test:test@" in settings.database_url.get_secret_value():
        pytest.skip("Admin bootstrap integration test requires configured PostgreSQL.")

    engine, connection, outer, session = await _test_session(settings)
    user_id = uuid.uuid4()
    password = "Synthetic-Bootstrap-Password-42"
    command = _command(user_id, password)
    try:
        admin_role = await _remove_admin_assignments(session)
        service = FirstAdminBootstrapService(
            UserRepository(session), AuditRepository(session), PasswordHasher()
        )
        result = await service.bootstrap(command, correlation_id=f"bootstrap-{user_id}")

        persisted_user = await session.get(UserORM, user_id)
        assert persisted_user is not None
        assert persisted_user.password_hash != password
        assert PasswordHasher().verify(password, persisted_user.password_hash)
        assignment = await session.scalar(
            select(UserRoleORM).where(
                UserRoleORM.user_id == user_id,
                UserRoleORM.role_id == admin_role.id,
            )
        )
        assert assignment is not None
        assert assignment.granted_by is None
        assert assignment.facility_id is None

        permission_codes = set(
            (
                await session.execute(
                    select(RolePermissionORM.permission_id).where(
                        RolePermissionORM.role_id == admin_role.id
                    )
                )
            )
            .scalars()
            .all()
        )
        expected_permissions = {
            permission.id
            for permission in await UserRepository(session).get_permissions_by_codes(
                {Permission.MANAGE_USERS.value, Permission.MANAGE_SYSTEM.value}
            )
        }
        assert expected_permissions <= permission_codes

        audit = await session.scalar(
            select(AuditLogORM).where(
                AuditLogORM.event_type == "admin_bootstrapped",
                AuditLogORM.target_id == user_id,
            )
        )
        assert audit is not None
        assert audit.actor_id is None
        assert audit.source == "bootstrap_cli"
        assert password not in str(audit.detail)
        assert persisted_user.password_hash not in str(audit.detail)

        app = create_app()

        async def override_session() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[_db_session_provider] = override_session
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": result.email, "password": password},
            )
            assert login.status_code == 200
            token = login.json()["access_token"]
            profile = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert profile.status_code == 200
            assert "admin" in profile.json()["roles"]
            assert {Permission.MANAGE_USERS.value, Permission.MANAGE_SYSTEM.value} <= set(
                profile.json()["permissions"]
            )

        with pytest.raises(ConflictError, match="already provisioned"):
            await service.bootstrap(
                _command(uuid.uuid4(), "Another-Synthetic-Password-42"),
                correlation_id="second-bootstrap",
            )
    finally:
        await session.close()
        if outer.is_active:
            await outer.rollback()
        await connection.close()
        await engine.dispose()


async def test_critical_audit_failure_rolls_back_user_and_role_assignment(
    settings: Settings,
) -> None:
    if "test:test@" in settings.database_url.get_secret_value():
        pytest.skip("Admin bootstrap integration test requires configured PostgreSQL.")

    engine, connection, outer, session = await _test_session(settings)
    user_id = uuid.uuid4()
    try:
        admin_role = await _remove_admin_assignments(session)
        admin_role_id = admin_role.id
        admin_permission_rows = await UserRepository(session).get_permissions_by_codes(
            {Permission.MANAGE_USERS.value, Permission.MANAGE_SYSTEM.value}
        )
        admin_permission_ids = {permission.id for permission in admin_permission_rows}
        await session.execute(
            delete(RolePermissionORM).where(
                RolePermissionORM.role_id == admin_role.id,
                RolePermissionORM.permission_id.in_(admin_permission_ids),
            )
        )
        await session.flush()
        savepoint = await session.begin_nested()
        audit_repo = AuditRepository(session)

        async def fail_audit(_entry: AuditLogORM) -> AuditLogORM:
            raise RuntimeError("synthetic audit failure")

        audit_repo.append = fail_audit  # type: ignore[method-assign]
        service = FirstAdminBootstrapService(UserRepository(session), audit_repo, PasswordHasher())
        with pytest.raises(RuntimeError, match="synthetic audit failure"):
            await service.bootstrap(
                _command(user_id, "Synthetic-Rollback-Password-42"),
                correlation_id=f"rollback-{user_id}",
            )
        await savepoint.rollback()
        session.expire_all()

        assert await session.get(UserORM, user_id) is None
        assert (
            await session.scalar(select(UserRoleORM).where(UserRoleORM.user_id == user_id)) is None
        )
        assert (
            await session.scalar(
                select(AuditLogORM).where(AuditLogORM.correlation_id == f"rollback-{user_id}")
            )
            is None
        )
        assert not set(
            (
                await session.execute(
                    select(RolePermissionORM.permission_id).where(
                        RolePermissionORM.role_id == admin_role_id,
                        RolePermissionORM.permission_id.in_(admin_permission_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
    finally:
        await session.close()
        if outer.is_active:
            await outer.rollback()
        await connection.close()
        await engine.dispose()
