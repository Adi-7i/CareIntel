"""Worker database initialization."""

import asyncio
from typing import Any

from celery.signals import worker_process_init, worker_process_shutdown

from careintel.core.config import get_settings
from careintel.core.database import build_engine, build_session_factory, dispose_engine

# Global state for worker processes
_engine: Any = None
_session_factory: Any = None


@worker_process_init.connect
def init_worker_db(**kwargs: Any) -> None:
    """Initialize DB connection pool when a worker process starts."""
    global _engine, _session_factory
    settings = get_settings()
    _engine = build_engine(settings)
    _session_factory = build_session_factory(_engine)


@worker_process_shutdown.connect
def shutdown_worker_db(**kwargs: Any) -> None:
    """Dispose of DB connection pool when a worker process shuts down."""
    global _engine
    if _engine:
        # Celery signals are synchronous, dispose_engine is async.
        # This is a bit tricky, we must run the async disposal.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(dispose_engine(_engine))
            else:
                loop.run_until_complete(dispose_engine(_engine))
        except Exception:
            pass


def get_session_factory() -> Any:
    """Get the session factory for the worker."""
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Ensure worker_process_init ran.")
    return _session_factory
