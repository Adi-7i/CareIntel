"""
Shared pytest fixtures and configuration for all test categories.

Fixture scopes:
- ``settings``: function scope — each test gets fresh settings with overrides.
- ``app``: function scope — fresh app instance per test.
- ``client``: function scope — ASGI test client.
- ``mock_engine``: function scope — mocked async engine for unit tests.

Integration tests (marked with @pytest.mark.integration) require
a live database and are skipped by default unless DATABASE_URL is set.

Environment isolation:
  Tests always run with APP_ENV=testing. Settings cache is cleared between
  tests to prevent cross-test contamination.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Force testing environment before any application import resolves settings
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/careintel_test"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-at-all")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-not-for-production")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    """Clear the settings LRU cache before each test to prevent contamination."""
    from careintel.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Any:
    """Return a Settings instance configured for testing."""
    from careintel.core.config import get_settings

    return get_settings()


@pytest.fixture
def mock_engine() -> MagicMock:
    """Return a MagicMock async engine for unit tests that don't need a real DB."""
    engine = MagicMock()
    engine.dispose = AsyncMock()
    return engine


@pytest.fixture
def mock_session_factory(mock_engine: MagicMock) -> MagicMock:
    """Return a mocked session factory."""
    return MagicMock()


@pytest.fixture
def app(mock_engine: MagicMock, mock_session_factory: MagicMock) -> Any:
    """
    Return a FastAPI test application instance.

    The database engine and session factory are replaced with mocks so
    API/unit tests do not require a live database.
    """
    from careintel.main import create_app

    test_app = create_app()
    # Override app.state so health/readiness checks use the mock engine
    test_app.state.db_engine = mock_engine
    test_app.state.db_session_factory = mock_session_factory
    return test_app


@pytest_asyncio.fixture
async def client(app: Any) -> AsyncGenerator[AsyncClient, None]:
    """
    Return an ASGI test client for API-level tests.

    Uses httpx.AsyncClient with ASGITransport — no network connection needed.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
