"""Interactive, one-time production bootstrap for the first CareIntel admin."""

from __future__ import annotations

import asyncio
import getpass
import sys
import uuid
from collections.abc import Callable

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from careintel.application.auth.admin_bootstrap_service import (
    AdminBootstrapScope,
    BootstrapAdminCommand,
    BootstrapAdminResult,
    FirstAdminBootstrapService,
)
from careintel.application.auth.password_hasher import PasswordHasher
from careintel.core.config import Environment, Settings, get_settings
from careintel.core.database import (
    build_engine,
    build_session_factory,
    dispose_engine,
    get_async_session,
)
from careintel.core.errors import CareIntelError, ValidationError
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.user_repo import UserRepository

InputFunction = Callable[[str], str]
PasswordFunction = Callable[[str], str]


def collect_command(
    *,
    input_fn: InputFunction = input,
    password_fn: PasswordFunction = getpass.getpass,
    user_id_factory: Callable[[], uuid.UUID] = uuid.uuid4,
) -> BootstrapAdminCommand:
    """Collect and validate non-secret operator intent without touching the database."""
    print("CareIntel Production Admin Bootstrap")
    print()
    email = input_fn("Email: ").strip()
    display_name = input_fn("Display name: ").strip()
    password = password_fn("Password: ")
    password_confirmation = password_fn("Confirm password: ")
    if password != password_confirmation:
        raise ValidationError("Password confirmation does not match.")

    scope = input_fn("Scope (type SYSTEM-WIDE to select the supported bootstrap scope): ")
    if scope.strip().casefold() != AdminBootstrapScope.SYSTEM_WIDE.value:
        raise ValidationError("System-wide scope was not explicitly selected.")

    return BootstrapAdminCommand(
        user_id=user_id_factory(),
        email=email,
        display_name=display_name,
        password=password,
        scope=AdminBootstrapScope.SYSTEM_WIDE,
    )


def confirm_command(command: BootstrapAdminCommand, *, input_fn: InputFunction = input) -> bool:
    """Display only safe fields and require an explicit operator confirmation."""
    print()
    print("Admin account prepared.")
    print(f"Email: {command.email}")
    print("Role: admin")
    print(f"Scope: {command.scope.value}")
    print(f"User ID: {command.user_id}")
    return input_fn("Create this administrator? [y/N] ").strip().casefold() in {"y", "yes"}


async def bootstrap(
    command: BootstrapAdminCommand,
    *,
    settings: Settings | None = None,
) -> BootstrapAdminResult:
    """Run the bootstrap inside the existing database unit-of-work boundary."""
    settings = settings or get_settings()
    if settings.app_env is not Environment.PRODUCTION:
        raise ValidationError("This command requires APP_ENV=production.")

    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    correlation_id = f"admin-bootstrap-{uuid.uuid4()}"
    try:
        async with get_async_session(session_factory) as session:
            service = FirstAdminBootstrapService(
                user_repo=UserRepository(session),
                audit_repo=AuditRepository(session),
                password_hasher=PasswordHasher(),
            )
            return await service.bootstrap(command, correlation_id=correlation_id)
    finally:
        await dispose_engine(engine)


def main() -> int:
    """CLI entrypoint. No command-line arguments, including passwords, are accepted."""
    if len(sys.argv) != 1:
        print("ERROR: This interactive command does not accept command-line arguments.")
        return 2
    try:
        settings = get_settings()
        if settings.app_env is not Environment.PRODUCTION:
            raise ValidationError("This command requires APP_ENV=production.")
        command = collect_command()
        if not confirm_command(command):
            print("Bootstrap cancelled. No changes were made.")
            return 1
        result = asyncio.run(bootstrap(command, settings=settings))
    except (IntegrityError, SQLAlchemyError):
        print("ERROR: Administrator bootstrap failed safely due to a database error.")
        return 1
    except CareIntelError as exc:
        print(f"ERROR: {exc.message}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nBootstrap cancelled. No changes were made.")
        return 1
    except Exception:
        print("ERROR: Administrator bootstrap failed safely due to an unexpected error.")
        return 1

    print()
    print("Administrator created successfully.")
    print(f"Email: {result.email}")
    print(f"Role: {result.role}")
    print(f"Scope: {result.scope}")
    print(f"User ID: {result.user_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
