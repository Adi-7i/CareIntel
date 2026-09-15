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
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.core.config import Settings, get_settings
from careintel.core.database import get_async_session

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
