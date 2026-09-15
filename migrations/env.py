"""
Alembic migration environment — async mode.

Key responsibilities:
1. Load DATABASE_URL from application settings (never from alembic.ini).
2. Configure the async SQLAlchemy engine.
3. Run migrations in 'online' mode using asyncio.
4. Provide a target_metadata hook so future autogenerate works correctly.

Design decisions:
- Uses asyncpg via create_async_engine; migrations run in an async event loop.
- Settings are loaded via get_settings() to keep credential management consistent.
- target_metadata is imported from a central declarative base (to be added in Step 2).
  Currently None — autogenerate will produce empty migrations until models exist.
"""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Ensure the src directory is on the path when running alembic directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import settings to get the database URL
from careintel.core.config import get_settings

# Alembic Config object — gives access to alembic.ini values
config = context.config

# Configure Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ──────────────────────────────────────────────────────────────────────────────
# target_metadata: used by --autogenerate to detect schema changes.
# Import your DeclarativeBase.metadata here once ORM models exist (Step 2+).
# ──────────────────────────────────────────────────────────────────────────────
# from careintel.persistence.models import Base  # uncomment in Step 2
target_metadata = None


def get_database_url() -> str:
    """Retrieve DATABASE_URL from application settings."""
    settings = get_settings()
    return settings.database_url.get_secret_value()


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for generating migration scripts for review or DBAs.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations within a sync connection (called from async context)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations online.

    NullPool is used so each migration run gets a fresh connection
    and connections are not held in a pool between runs.
    """
    url = get_database_url()
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
