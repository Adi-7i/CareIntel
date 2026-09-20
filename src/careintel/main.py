"""
CareIntel — Application composition root.

This file is intentionally thin. Its only responsibility is:
1. Configure infrastructure (logging, settings).
2. Create the FastAPI application instance.
3. Register middleware, exception handlers, and routers.
4. Manage the lifespan (startup/shutdown hooks for database, etc.).

No business logic, SQL, validation logic, or provider calls belong here.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from careintel.api.v1.router import router as v1_router
from careintel.core.config import get_settings
from careintel.core.correlation import CorrelationIDMiddleware
from careintel.core.database import build_engine, build_session_factory, dispose_engine
from careintel.core.errors import register_exception_handlers
from careintel.core.logging import configure_logging, get_logger
from careintel.infrastructure.scanner.noop_scanner import NoOpScanner
from careintel.infrastructure.storage.azure_provider import AzureBlobProvider
from careintel.infrastructure.storage.fake_provider import FakeBlobProvider


def create_app() -> FastAPI:
    """
    Application factory.

    Returns a fully configured FastAPI instance. Calling this function
    multiple times (e.g. in tests) produces independent application instances.
    """
    settings = get_settings()
    configure_logging(settings)
    logger = get_logger(__name__)

    # ── Lifespan ──────────────────────────────────────────────────────────────
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        """Manage startup and shutdown of shared resources."""
        logger.info(
            "CareIntel starting up",
            extra={
                "env": settings.app_env.value,
                "database": settings.database_url_safe(),
            },
        )

        # Build the async engine and session factory; store on app.state so
        # dependency providers can retrieve them without global state.
        engine = build_engine(settings)
        session_factory = build_session_factory(engine)
        _app.state.db_engine = engine
        _app.state.db_session_factory = session_factory

        # Initialize Storage Provider
        if settings.azure_storage_connection_string:
            _app.state.blob_provider = AzureBlobProvider(
                connection_string=settings.azure_storage_connection_string.get_secret_value(),
                container_name=settings.azure_storage_container,
            )
        else:
            _app.state.blob_provider = FakeBlobProvider()

        # Initialize Scanner
        _app.state.content_scanner = NoOpScanner()

        logger.info("CareIntel startup complete — ready to serve traffic")
        yield

        # ── Shutdown ─────────────────────────────────────────────────────────
        logger.info("CareIntel shutting down — disposing resources")
        await dispose_engine(engine)
        logger.info("CareIntel shutdown complete")

    # ── Application instance ───────────────────────────────────────────────
    app = FastAPI(
        title="CareIntel API",
        description=(
            "Non-diagnostic healthcare information and reviewer-workflow system. "
            "All clinical decisions remain with qualified human reviewers."
        ),
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
        # Disable default exception handlers; we register our own below.
        # (FastAPI still registers its own 422 handler; our handler overrides it.)
    )

    # ── Middleware (order matters — outermost applied last, runs first) ──────
    # CORS — must be before correlation ID so pre-flight requests pass through
    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["*"],
        )

    # Correlation ID — assigns/propagates X-Correlation-ID on every request
    app.add_middleware(CorrelationIDMiddleware)

    # ── Exception handlers ─────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ────────────────────────────────────────────────────────────
    app.include_router(v1_router)

    logger.info("CareIntel application configured", extra={"routes": len(app.routes)})
    return app


# Module-level app instance — used by uvicorn and ASGI test clients.
app = create_app()
