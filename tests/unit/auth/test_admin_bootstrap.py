from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from careintel.application.auth.admin_bootstrap_service import (
    AdminBootstrapScope,
    BootstrapAdminCommand,
    BootstrapAdminResult,
    FirstAdminBootstrapService,
)
from careintel.application.auth.password_hasher import PasswordHasher
from careintel.core.config import Environment
from careintel.core.errors import ConflictError, ValidationError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy


def _command(*, email: str = "first-admin@example.com") -> BootstrapAdminCommand:
    return BootstrapAdminCommand(
        user_id=uuid.uuid4(),
        email=email,
        display_name="First Administrator",
        password="Synthetic-Admin-Password-42",
        scope=AdminBootstrapScope.SYSTEM_WIDE,
    )


def _service() -> tuple[FirstAdminBootstrapService, AsyncMock, AsyncMock]:
    repo = AsyncMock()
    role_id = uuid.uuid4()
    repo.get_role_by_name_for_update.return_value = SimpleNamespace(id=role_id, name="admin")
    repo.role_has_assignment.return_value = False
    repo.get_by_email.return_value = None
    repo.get_permissions_by_codes.return_value = [
        SimpleNamespace(id=uuid.uuid4(), code=Permission.MANAGE_USERS.value),
        SimpleNamespace(id=uuid.uuid4(), code=Permission.MANAGE_SYSTEM.value),
    ]
    repo.create.side_effect = lambda user: user
    repo.assign_role.side_effect = lambda assignment: assignment
    audit = AsyncMock()
    return FirstAdminBootstrapService(repo, audit, PasswordHasher()), repo, audit


@pytest.mark.unit
async def test_first_admin_bootstrap_hashes_password_assigns_role_permissions_and_audit() -> None:
    service, repo, audit = _service()
    command = _command()

    result = await service.bootstrap(command, correlation_id="bootstrap-correlation")

    user = repo.create.await_args.args[0]
    assert user.id == command.user_id
    assert user.email == command.email
    assert user.display_name == command.display_name
    assert user.is_active is True
    assert user.is_verified is True
    assert user.password_hash != command.password
    assert PasswordHasher().verify(command.password, user.password_hash)

    assignment = repo.assign_role.await_args.args[0]
    assert assignment.user_id == command.user_id
    assert assignment.role_id == repo.get_role_by_name_for_update.return_value.id
    assert assignment.granted_by is None
    assert assignment.facility_id is None
    repo.ensure_role_permissions.assert_awaited_once()

    assert result.permissions == {
        Permission.MANAGE_USERS.value,
        Permission.MANAGE_SYSTEM.value,
    }
    actor = UserContext(
        id=result.user_id,
        is_active=True,
        roles={result.role},
        permissions=set(result.permissions),
        role_facilities={result.role: None},
    )
    assert AuthorizationPolicy.evaluate(actor, Permission.MANAGE_USERS)
    assert AuthorizationPolicy.evaluate(
        actor,
        Permission.MANAGE_SYSTEM,
        facility_scope=uuid.uuid4(),
    )

    audit_entry = audit.append.await_args.args[0]
    assert audit_entry.event_type == AuditEventType.ADMIN_BOOTSTRAPPED
    assert audit_entry.actor_id is None
    assert audit_entry.target_id == command.user_id
    assert audit_entry.source == "bootstrap_cli"
    assert audit_entry.detail == {
        "action": "bootstrap_first_admin",
        "role": "admin",
        "scope": "system-wide",
    }
    assert command.password not in repr(command)
    assert command.password not in str(audit_entry.detail)
    assert user.password_hash not in str(audit_entry.detail)


@pytest.mark.unit
async def test_existing_admin_fails_closed_before_user_or_audit_write() -> None:
    service, repo, audit = _service()
    repo.role_has_assignment.return_value = True

    with pytest.raises(ConflictError, match="already provisioned"):
        await service.bootstrap(_command(), correlation_id="bootstrap-correlation")

    repo.get_by_email.assert_not_awaited()
    repo.create.assert_not_awaited()
    repo.assign_role.assert_not_awaited()
    audit.append.assert_not_awaited()


@pytest.mark.unit
async def test_duplicate_email_fails_closed() -> None:
    service, repo, audit = _service()
    repo.get_by_email.return_value = SimpleNamespace(id=uuid.uuid4())

    with pytest.raises(ConflictError, match="email already exists"):
        await service.bootstrap(_command(), correlation_id="bootstrap-correlation")

    repo.create.assert_not_awaited()
    repo.assign_role.assert_not_awaited()
    audit.append.assert_not_awaited()


@pytest.mark.unit
async def test_missing_admin_permission_definition_fails_before_write() -> None:
    service, repo, audit = _service()
    repo.get_permissions_by_codes.return_value = [
        SimpleNamespace(id=uuid.uuid4(), code=Permission.MANAGE_USERS.value)
    ]

    with pytest.raises(ValidationError, match="permission definitions"):
        await service.bootstrap(_command(), correlation_id="bootstrap-correlation")

    repo.ensure_role_permissions.assert_not_awaited()
    repo.create.assert_not_awaited()
    audit.append.assert_not_awaited()


@pytest.mark.unit
def test_cli_prompt_never_outputs_password_or_hash(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.bootstrap_admin import collect_command, confirm_command

    secret = "Synthetic-Admin-Password-42"
    answers = iter(["first-admin@example.com", "First Administrator", "SYSTEM-WIDE"])
    password_answers = iter([secret, secret])
    confirmation = iter(["yes"])

    command = collect_command(
        input_fn=lambda _prompt: next(answers),
        password_fn=lambda _prompt: next(password_answers),
        user_id_factory=lambda: uuid.UUID("00000000-0000-0000-0000-000000000111"),
    )
    assert confirm_command(command, input_fn=lambda _prompt: next(confirmation))

    output = capsys.readouterr().out
    assert secret not in output
    assert PasswordHasher().hash(secret) not in output
    assert "Role: admin" in output
    assert "Scope: system-wide" in output


@pytest.mark.unit
def test_cli_rejects_mismatched_password_confirmation() -> None:
    from scripts.bootstrap_admin import collect_command

    answers = iter(["first-admin@example.com", "First Administrator"])
    password_answers = iter(["Synthetic-Admin-Password-42", "different-password"])

    with pytest.raises(ValidationError, match="does not match"):
        collect_command(
            input_fn=lambda _prompt: next(answers),
            password_fn=lambda _prompt: next(password_answers),
        )


@pytest.mark.unit
def test_cli_requires_production_before_prompting(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts import bootstrap_admin

    monkeypatch.setattr(bootstrap_admin.sys, "argv", ["bootstrap_admin"])
    prompt = MagicPrompt()
    monkeypatch.setattr(bootstrap_admin, "collect_command", prompt)

    assert bootstrap_admin.main() == 1
    assert not prompt.called
    assert "requires APP_ENV=production" in capsys.readouterr().out


@pytest.mark.unit
def test_cli_main_confirms_and_reports_only_secret_free_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts import bootstrap_admin

    command = _command()
    result = BootstrapAdminResult(
        user_id=command.user_id,
        email=command.email,
        role="admin",
        scope="system-wide",
        permissions=frozenset({Permission.MANAGE_USERS.value, Permission.MANAGE_SYSTEM.value}),
    )
    observed: dict[str, object] = {}

    async def run_bootstrap(
        supplied_command: BootstrapAdminCommand,
        *,
        settings: object,
    ) -> BootstrapAdminResult:
        observed["command"] = supplied_command
        observed["settings"] = settings
        return result

    production_settings = SimpleNamespace(app_env=Environment.PRODUCTION)
    monkeypatch.setattr(bootstrap_admin.sys, "argv", ["bootstrap_admin"])
    monkeypatch.setattr(bootstrap_admin, "get_settings", lambda: production_settings)
    monkeypatch.setattr(bootstrap_admin, "collect_command", lambda: command)
    monkeypatch.setattr(bootstrap_admin, "confirm_command", lambda _command: True)
    monkeypatch.setattr(bootstrap_admin, "bootstrap", run_bootstrap)

    assert bootstrap_admin.main() == 0
    assert observed == {"command": command, "settings": production_settings}
    output = capsys.readouterr().out
    assert "Administrator created successfully." in output
    assert command.password not in output
    assert "Role: admin" in output
    assert "Scope: system-wide" in output


class MagicPrompt:
    def __init__(self) -> None:
        self.called = False

    def __call__(self) -> BootstrapAdminCommand:
        self.called = True
        return _command()
