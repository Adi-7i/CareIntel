"""
Async SQLAlchemy engine and session management.

Design decisions:
- Single async engine created at startup, shared for the lifetime of the process.
- Sessions are request-scoped: created per-request, committed/rolled-back per-request.
- Engine and session factory are NOT global singletons accessible anywhere;
  they are wired through FastAPI dependency injection (see api/deps.py).
- ``create_async_engine`` with NullPool is used for migrations (Alembic),
  so connection management is explicit and safe.
- No ORM models are defined here — this module owns only infrastructure.

Usage:
    # In API dependency:
    from careintel.core.database import get_async_session
    async with get_async_session(engine) as session:
        ...

    # As FastAPI dependency (via api/deps.py):
    async def endpoint(session: AsyncSession = Depends(get_db)):
        ...
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from careintel.core.config import Settings
from careintel.core.logging import get_logger

logger = get_logger(__name__)


def build_engine(settings: Settings) -> AsyncEngine:
    """
    Create and return the async SQLAlchemy engine.

    The engine is created once at application startup and is
    safe to share across all requests. Pool configuration comes from settings.
    """
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_pre_ping=True,  # Verify connections before use (handles stale connections)
        echo=settings.database_echo_sql,
        # Connection args: statement_timeout guards against runaway queries.
        # Values are intentionally conservative; tune per-query in application layer.
        connect_args={
            "server_settings": {
                "application_name": "careintel",
                "statement_timeout": "30000",  # 30 seconds max per statement
            }
        },
    )

    logger.info(
        "Database engine created",
        extra={
            "driver": "asyncpg",
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "database": settings.database_url_safe(),
        },
    )
    return engine


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create a session factory bound to the provided engine.

    expire_on_commit=False: prevents lazy-load errors after commit when
    response serialization accesses model attributes.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@asynccontextmanager
async def get_async_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for a single database session.

    - Commits on clean exit.
    - Rolls back on any exception, then re-raises.
    - Closes the session in all cases (releases connection to pool).

    Usage:
        async with get_async_session(session_factory) as session:
            result = await session.execute(...)
    """
    session: AsyncSession = session_factory()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Database session error — rolling back transaction")
        raise
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def check_database_liveness(engine: AsyncEngine) -> bool:
    """
    Execute a minimal connectivity probe: ``SELECT 1``.

    Returns True if the database is reachable, False otherwise.
    Does not raise — callers (health endpoints) interpret the bool.
    """
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("Database liveness probe failed", exc_info=True)
        return False


async def dispose_engine(engine: AsyncEngine) -> None:
    """
    Gracefully dispose of the engine's connection pool.

    Call during application shutdown to release all connections cleanly.
    """
    await engine.dispose()
    logger.info("Database engine disposed")
