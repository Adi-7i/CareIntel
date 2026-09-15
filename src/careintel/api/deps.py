"""
Shared FastAPI dependency providers for the API layer.

All dependencies follow FastAPI's Depends() pattern.
Route handlers declare what they need; this module wires the concrete implementations.

Rules:
- Dependency providers must NOT contain business logic.
- Database sessions are created here and injected; route handlers never access
  the session factory or engine directly.
- Settings are injected via Depends; route handlers never call get_settings() directly.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.auth.auth_service import AuthService
from careintel.application.auth.password_hasher import PasswordHasher
from careintel.application.auth.permission_service import PermissionService
from careintel.application.auth.token_service import JWTService
from careintel.core.config import Settings, get_settings
from careintel.core.database import get_async_session
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.session_repo import SessionRepository
from careintel.persistence.repositories.user_repo import UserRepository

# Using FastAPI's built-in HTTPBearer for token extraction (swagger integration)
token_bearer = HTTPBearer(auto_error=False)

# ── Settings ──────────────────────────────────────────────────────────────────


def _settings_provider() -> Settings:
    """Inject application settings."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(_settings_provider)]


# ── Database Session ───────────────────────────────────────────────────────────


async def _db_session_provider(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Inject a request-scoped async database session.

    The session factory is stored on app.state during startup.
    Commits on clean exit; rolls back and closes on error.
    """
    session_factory = request.app.state.db_session_factory
    async with get_async_session(session_factory) as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(_db_session_provider)]


# ── Authentication & Authorization ─────────────────────────────────────────────


def get_auth_service(
    session: DbSessionDep,
    settings: SettingsDep,
) -> AuthService:
    """Provide the AuthService."""
    return AuthService(
        user_repo=UserRepository(session),
        session_repo=SessionRepository(session),
        audit_repo=AuditRepository(session),
        token_service=JWTService(settings),
        hasher=PasswordHasher(),
    )


async def get_optional_user(
    token_cred: Annotated[HTTPAuthorizationCredentials | None, Depends(token_bearer)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserContext | None:
    """Extract and validate the current user from token, if provided."""
    if not token_cred:
        return None
    try:
        return await auth_service.get_current_user(token_cred.credentials)
    except Exception:
        # If optional, we ignore auth errors
        return None


async def get_current_user(
    token_cred: Annotated[HTTPAuthorizationCredentials | None, Depends(token_bearer)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserContext:
    """Extract and validate the current user from token. Raises 401 if missing/invalid."""
    from careintel.core.errors import AuthError

    if not token_cred:
        raise AuthError("Authentication credentials are required.")

    return await auth_service.get_current_user(token_cred.credentials)


async def get_raw_token(
    token_cred: Annotated[HTTPAuthorizationCredentials | None, Depends(token_bearer)],
) -> str:
    """Extract the raw token string from the request."""
    from careintel.core.errors import AuthError

    if not token_cred:
        raise AuthError("Authentication credentials are required.")
    return token_cred.credentials


CurrentUserDep = Annotated[UserContext, Depends(get_current_user)]
OptionalUserDep = Annotated[UserContext | None, Depends(get_optional_user)]
RawTokenDep = Annotated[str, Depends(get_raw_token)]


def require_permission(permission: Permission | str) -> Any:
    """
    Dependency factory to enforce RBAC permissions.
    """

    async def _require_permission(user: CurrentUserDep) -> None:
        PermissionService.check(actor=user, action=permission)

    return Depends(_require_permission)
