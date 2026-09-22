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
from careintel.infrastructure.extraction.demo_provider import DemoExtractionProvider
from careintel.infrastructure.language.demo_provider import DemoLanguageProvider
from careintel.infrastructure.ocr.demo_provider import DemoOcrProvider
from careintel.infrastructure.scanner.noop_scanner import NoOpScanner
from careintel.infrastructure.storage.azure_provider import AzureBlobProvider
from careintel.infrastructure.storage.fake_provider import FakeBlobProvider
from careintel.infrastructure.stt.demo_provider import DemoSpeechProvider
from careintel.infrastructure.translation.demo_provider import DemoTranslationProvider


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
            provider = AzureBlobProvider(
                connection_string=settings.azure_storage_connection_string.get_secret_value(),
                container_name=settings.azure_storage_container,
            )
            await provider.ensure_container()
            _app.state.blob_provider = provider
        else:
            _app.state.blob_provider = FakeBlobProvider()

        # Initialize Scanner
        _app.state.content_scanner = NoOpScanner()

        # Initialize Providers
        # ── LLM Provider ──────────────────────────────────────────────────────────
        if settings.llm_provider == "azure_openai" and settings.azure_openai_api_key:
            from careintel.infrastructure.ai.azure_openai_adapter import AzureOpenAIAdapter

            _app.state.llm_provider = AzureOpenAIAdapter(
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key.get_secret_value(),
                deployment=settings.azure_llm_deployment,
                api_version=settings.azure_llm_api_version,
            )
        else:
            from careintel.infrastructure.ai.demo_adapter import DemoLLMProvider

            _app.state.llm_provider = DemoLLMProvider()

        # ── Embedding Provider ────────────────────────────────────────────────────
        if settings.embedding_provider == "azure_openai" and settings.azure_openai_api_key:
            from careintel.infrastructure.embedding.azure_provider import AzureEmbeddingProvider

            _app.state.embedding_provider = AzureEmbeddingProvider(
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key.get_secret_value(),
                deployment=settings.azure_embedding_deployment,
            )
        else:
            from careintel.infrastructure.embedding.demo_provider import DemoEmbeddingProvider

            _app.state.embedding_provider = DemoEmbeddingProvider()

        # ── STT Provider ──────────────────────────────────────────────────────────
        if (
            settings.stt_provider in ("azure_openai_transcribe", "azure_openai_diarize")
            and settings.azure_openai_api_key
        ):
            from careintel.infrastructure.stt.azure_provider import AzureSpeechProvider

            mode = "diarize" if settings.stt_provider == "azure_openai_diarize" else "transcribe"
            deployment = (
                settings.azure_stt_diarize_deployment
                if mode == "diarize"
                else settings.azure_stt_deployment
            )
            api_version = (
                settings.azure_stt_diarize_api_version
                if mode == "diarize"
                else settings.azure_stt_api_version
            )
            from typing import Literal, cast

            _app.state.speech_provider = AzureSpeechProvider(
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key.get_secret_value(),
                api_version=api_version,
                deployment=deployment,
                mode=cast(Literal["transcribe", "diarize"], mode),
            )
        else:
            _app.state.speech_provider = DemoSpeechProvider()

        # ── TTS Provider ──────────────────────────────────────────────────────────
        if settings.tts_provider == "azure_openai" and settings.azure_openai_api_key:
            from careintel.infrastructure.tts.azure_provider import AzureTTSProvider

            _app.state.tts_provider = AzureTTSProvider(
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key.get_secret_value(),
                api_version=settings.azure_tts_api_version,
                deployment=settings.azure_tts_deployment,
                default_voice=settings.azure_tts_voice,
            )
        else:
            from careintel.infrastructure.tts.demo_provider import DemoTTSProvider

            _app.state.tts_provider = DemoTTSProvider()

        # ── OCR Provider ──────────────────────────────────────────────────────────
        if (
            settings.ocr_provider == "azure_document_intelligence"
            and settings.azure_document_intelligence_endpoint
            and settings.azure_document_intelligence_key
        ):
            from careintel.infrastructure.ocr.azure_provider import (
                AzureDocumentIntelligenceProvider,
            )

            _app.state.ocr_provider = AzureDocumentIntelligenceProvider(
                endpoint=settings.azure_document_intelligence_endpoint,
                key=settings.azure_document_intelligence_key.get_secret_value(),
                model=settings.azure_di_model,
            )
        else:
            _app.state.ocr_provider = DemoOcrProvider()

        # Other Demo Providers
        _app.state.language_provider = DemoLanguageProvider()
        _app.state.translation_provider = DemoTranslationProvider()
        _app.state.extraction_provider = DemoExtractionProvider()

        logger.info("CareIntel startup complete — ready to serve traffic")
        try:
            yield
        finally:
            # ── Shutdown ─────────────────────────────────────────────────────
            logger.info("CareIntel shutting down — disposing resources")
            await _app.state.blob_provider.close()
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

    logger.info("CareIntel application configured")
    return app


# Module-level app instance — used by uvicorn and ASGI test clients.
app = create_app()
