"""One-time, CLI-only first administrator bootstrap service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import EmailStr, TypeAdapter
from pydantic import ValidationError as PydanticValidationError

from careintel.application.auth.password_hasher import PasswordHasher
from careintel.core.errors import ConflictError, ValidationError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.roles import Role
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.user import UserORM, UserRoleORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.user_repo import UserRepository

_EMAIL_ADAPTER = TypeAdapter(EmailStr)
_BCRYPT_MAX_PASSWORD_BYTES = 72


class AdminBootstrapScope(StrEnum):
    """Scopes supported by the first-admin bootstrap contract."""

    SYSTEM_WIDE = "system-wide"


@dataclass(frozen=True)
class BootstrapAdminCommand:
    """Validated operator intent passed from the interactive CLI."""

    user_id: uuid.UUID
    email: str
    display_name: str
    password: str = field(repr=False)
    scope: AdminBootstrapScope


@dataclass(frozen=True)
class BootstrapAdminResult:
    """Secret-free result safe for CLI output."""

    user_id: uuid.UUID
    email: str
    role: str
    scope: str
    permissions: frozenset[str]


class FirstAdminBootstrapService:
    """Atomically provision the first system-wide CareIntel administrator."""

    REQUIRED_ADMIN_PERMISSIONS = frozenset(
        {
            Permission.MANAGE_USERS.value,
            Permission.MANAGE_SYSTEM.value,
        }
    )

    def __init__(
        self,
        user_repo: UserRepository,
        audit_repo: AuditRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._users = user_repo
        self._audit = audit_repo
        self._hasher = password_hasher

    @staticmethod
    def _validate(command: BootstrapAdminCommand) -> tuple[str, str]:
        if command.scope is not AdminBootstrapScope.SYSTEM_WIDE:
            raise ValidationError("Only an explicitly selected system-wide scope is supported.")
        try:
            email = str(_EMAIL_ADAPTER.validate_python(command.email)).casefold()
        except PydanticValidationError as exc:
            raise ValidationError("A valid administrator email is required.") from exc
        display_name = command.display_name.strip()
        if not display_name:
            raise ValidationError("Administrator display name is required.")
        password_bytes = command.password.encode("utf-8")
        if len(command.password) < 12:
            raise ValidationError("Administrator password must contain at least 12 characters.")
        if len(password_bytes) > _BCRYPT_MAX_PASSWORD_BYTES:
            raise ValidationError("Administrator password is too long for the password hasher.")
        return email, display_name

    async def bootstrap(
        self,
        command: BootstrapAdminCommand,
        *,
        correlation_id: str,
    ) -> BootstrapAdminResult:
        """Create the first admin without committing the caller-owned transaction."""
        email, display_name = self._validate(command)

        # Locking the stable role row serializes concurrent first-admin attempts.
        # Under PostgreSQL READ COMMITTED, the second waiter re-checks assignments
        # after the first transaction commits and fails closed.
        admin_role = await self._users.get_role_by_name_for_update(Role.ADMIN.value)
        if admin_role is None:
            raise ValidationError("The administrator role is unavailable; apply migrations first.")
        if await self._users.role_has_assignment(admin_role.id):
            raise ConflictError("An administrator is already provisioned; bootstrap refused.")
        if await self._users.get_by_email(email) is not None:
            raise ConflictError("A user with this email already exists; bootstrap refused.")

        permission_rows = await self._users.get_permissions_by_codes(
            set(self.REQUIRED_ADMIN_PERMISSIONS)
        )
        observed_permissions = {permission.code for permission in permission_rows}
        missing_permissions = self.REQUIRED_ADMIN_PERMISSIONS - observed_permissions
        if missing_permissions:
            raise ValidationError(
                "Required administrator permission definitions are unavailable; "
                "apply migrations first."
            )
        await self._users.ensure_role_permissions(admin_role.id, permission_rows)

        user = await self._users.create(
            UserORM(
                id=command.user_id,
                email=email,
                display_name=display_name,
                password_hash=self._hasher.hash(command.password),
                is_active=True,
                # A deliberately operator-provisioned identity is verified at creation.
                # Login currently checks is_active; retaining this explicit flag avoids
                # an ambiguous account state for future verification enforcement.
                is_verified=True,
            )
        )
        await self._users.assign_role(
            UserRoleORM(
                user_id=user.id,
                role_id=admin_role.id,
                granted_by=None,
                facility_id=None,
            )
        )
        await self._audit.append(
            AuditLogORM(
                event_type=AuditEventType.ADMIN_BOOTSTRAPPED,
                actor_id=None,
                target_id=user.id,
                target_type="user",
                correlation_id=correlation_id,
                source="bootstrap_cli",
                outcome="SUCCESS",
                detail={
                    "action": "bootstrap_first_admin",
                    "role": Role.ADMIN.value,
                    "scope": AdminBootstrapScope.SYSTEM_WIDE.value,
                },
            )
        )
        return BootstrapAdminResult(
            user_id=user.id,
            email=user.email,
            role=Role.ADMIN.value,
            scope=AdminBootstrapScope.SYSTEM_WIDE.value,
            permissions=self.REQUIRED_ADMIN_PERMISSIONS,
        )
