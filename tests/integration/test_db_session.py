"""
Integration tests for database session management.

These tests require a live PostgreSQL database and are skipped
unless the DATABASE_URL environment variable points to a real instance.

Run with:
    uv run pytest tests/integration/ -m integration -v
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration

# Skip all integration tests if DATABASE_URL is a test placeholder
_DB_URL = os.environ.get("DATABASE_URL", "")
_REQUIRES_REAL_DB = pytest.mark.skipif(
    "test:test@" in _DB_URL or not _DB_URL,
    reason="Integration tests require a real DATABASE_URL. "
    "Set DATABASE_URL env var to a live PostgreSQL instance.",
)


@_REQUIRES_REAL_DB
class TestDatabaseConnectivity:
    """Tests that require a live database connection."""

    async def test_engine_connects_successfully(self, settings: object) -> None:
        """Can create an engine and execute SELECT 1."""
        from careintel.core.database import build_engine, check_database_liveness

        engine = build_engine(settings)  # type: ignore[arg-type]
        try:
            result = await check_database_liveness(engine)
            assert result is True, "Database liveness probe failed"
        finally:
            await engine.dispose()

    async def test_session_commits_and_closes(self, settings: object) -> None:
        """Session context manager commits and closes without error."""
        from sqlalchemy import text

        from careintel.core.database import (
            build_engine,
            build_session_factory,
            get_async_session,
        )

        engine = build_engine(settings)  # type: ignore[arg-type]
        session_factory = build_session_factory(engine)
        try:
            async with get_async_session(session_factory) as session:
                result = await session.execute(text("SELECT 1 AS probe"))
                row = result.fetchone()
                assert row is not None
                assert row[0] == 1
        finally:
            await engine.dispose()
