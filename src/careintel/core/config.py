"""
Typed application configuration via Pydantic Settings.

All configuration is sourced from environment variables (or .env files).
No secrets are ever hardcoded or defaulted to real values.

Usage:
    from careintel.core.config import get_settings

    settings = get_settings()
"""

from __future__ import annotations

import functools
from enum import StrEnum
from typing import Annotated

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Known deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Application settings.

    Loaded once at startup; immutable at runtime.
    All fields are typed; sensitive fields use SecretStr.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Validate on assignment so mis-configuration is caught eagerly
        validate_default=True,
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment name.",
    )
    app_debug: bool = Field(
        default=False,
        description="Enable debug mode. Must be False in production.",
    )
    app_host: str = Field(default="127.0.0.1", description="Bind address for uvicorn.")
    app_port: Annotated[int, Field(ge=1, le=65535)] = Field(
        default=8000,
        description="Bind port for uvicorn.",
    )
    app_log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Application log level.",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: SecretStr = Field(
        ...,
        description=(
            "Async PostgreSQL DSN. Format: postgresql+asyncpg://user:pass@host:port/dbname"
        ),
    )
    database_pool_size: Annotated[int, Field(ge=1, le=50)] = Field(
        default=10,
        description="SQLAlchemy async connection pool size.",
    )
    database_max_overflow: Annotated[int, Field(ge=0, le=50)] = Field(
        default=5,
        description="Max connections beyond pool_size.",
    )
    database_pool_timeout: Annotated[int, Field(ge=1, le=300)] = Field(
        default=30,
        description="Seconds to wait for a connection from the pool.",
    )
    database_echo_sql: bool = Field(
        default=False,
        description="Echo all SQL to stdout. Never enable in production.",
    )

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: SecretStr = Field(
        ...,
        description="HMAC secret key. Must be long and random in production.",
    )

    # ── JWT Authentication ───────────────────────────────────────────────────
    jwt_secret_key: SecretStr = Field(
        ...,
        description="Secret key specifically for JWT signing. Must be secure and random.",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm (e.g., HS256, RS256).",
    )
    jwt_access_token_ttl_minutes: Annotated[int, Field(ge=1, le=1440)] = Field(
        default=30,
        description="Access token time-to-live in minutes (max 24h).",
    )
    jwt_issuer: str = Field(
        default="careintel",
        description="The 'iss' claim in the JWT identifying the token issuer.",
    )
    jwt_audience: str = Field(
        default="careintel-api",
        description="The 'aud' claim in the JWT identifying intended recipients.",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_allowed_origins: list[str] = Field(
        default_factory=list,
        description="List of permitted CORS origins.",
    )

    # ── Evidence & Storage ───────────────────────────────────────────────────
    azure_storage_connection_string: SecretStr | None = Field(
        default=None,
        description="Azure Blob Storage connection string. If None, uses FakeBlobProvider.",
    )
    azure_storage_container: str = Field(
        default="careintel-evidence",
        description="Azure Blob Storage private container name.",
    )
    evidence_max_file_size_bytes: int = Field(
        default=52428800,
        description="Max upload file size in bytes (default 50MB).",
    )
    evidence_allowed_extensions: list[str] = Field(
        default_factory=lambda: [
            ".pdf",
            ".docx",
            ".txt",
            ".jpg",
            ".jpeg",
            ".png",
            ".mp3",
            ".wav",
            ".m4a",
            ".ogg",
        ],
        description="Allowed file extensions for upload.",
    )
    evidence_sas_ttl_minutes: int = Field(
        default=15,
        description="TTL in minutes for generated SAS download URLs.",
    )
    evidence_require_scan_before_ready: bool = Field(
        default=True,
        description="If True, evidence cannot become READY until scanned and CLEAN.",
    )

    # ── Processing & Providers ───────────────────────────────────────────────
    ocr_provider: str = Field(
        default="demo",
        description="OCR provider: demo, paddle, azure_doc_intelligence",
    )
    ocr_temp_workspace: str = Field(
        default="/tmp/careintel_ocr",  # noqa: S108
        description="Temporary workspace for OCR operations.",
    )

    stt_provider: str = Field(
        default="demo",
        description="STT provider: demo, azure_speech, whisper",
    )

    language_detection_provider: str = Field(
        default="demo",
        description="Language detection provider: demo, langdetect",
    )

    translation_provider: str = Field(
        default="demo",
        description="Translation provider: demo, azure_translate, deepl",
    )
    translation_api_key: SecretStr | None = Field(
        default=None,
        description="API key for translation provider if required.",
    )
    translation_endpoint: str | None = Field(
        default=None,
        description="Endpoint for translation provider if required.",
    )

    extraction_provider: str = Field(
        default="demo",
        description="Extraction provider: demo, gpt",
    )

    # ── Async Execution & Celery (Phase 8) ────────────
    celery_broker_url: SecretStr = Field(default=SecretStr("redis://localhost:6379/0"))
    celery_result_backend: SecretStr | None = Field(default=None)
    celery_task_default_queue: str = Field(default="careintel_default")
    celery_worker_prefetch_multiplier: int = Field(default=1)
    celery_task_soft_time_limit: int = Field(default=300)
    celery_task_hard_time_limit: int = Field(default=360)
    celery_stale_task_threshold_seconds: int = Field(default=120)

    # ── Structuring ──────────────────────────────────────────────────────────
    structuring_checklist_path: str = Field(
        default="config/checklists/demo_v1.json",
        description="Path to active checklist policy file",
    )
    structuring_active_checklist_version: str = Field(
        default="demo_v1",
        description="Active checklist version key",
    )
    structuring_max_questions_per_round: int = Field(
        default=5,
        description="Max clarification questions per round (prototype policy)",
    )
    structuring_max_rounds: int = Field(
        default=2,
        description="Max clarification rounds (prototype policy)",
    )

    # ── Validators ───────────────────────────────────────────────────────────
    @field_validator("database_url", mode="before")
    @classmethod
    def _validate_database_url(cls, v: object) -> object:
        """Reject sync driver schemes early."""
        raw = str(v)
        if raw.startswith("postgresql://") or raw.startswith("postgres://"):
            raise ValueError(
                "DATABASE_URL must use the asyncpg driver scheme: "
                "'postgresql+asyncpg://...'. "
                "Received a synchronous scheme which is incompatible with the async engine."
            )
        return v

    @model_validator(mode="after")
    def _reject_debug_in_production(self) -> Settings:
        """Hard-fail if debug mode is enabled in production."""
        if self.app_env == Environment.PRODUCTION and self.app_debug:
            raise ValueError("app_debug must be False when app_env is 'production'.")
        return self

    @model_validator(mode="after")
    def _reject_sql_echo_in_production(self) -> Settings:
        """Hard-fail if SQL echo is enabled in production."""
        if self.app_env == Environment.PRODUCTION and self.database_echo_sql:
            raise ValueError("database_echo_sql must be False when app_env is 'production'.")
        return self

    # ── Convenience properties ────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        """True when running in production."""
        return self.app_env == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """True when running in the test suite."""
        return self.app_env == Environment.TESTING

    def database_url_safe(self) -> str:
        """Return database URL with credentials masked — safe for logging."""
        import re

        raw = self.database_url.get_secret_value()
        # Replace user:password@ with ***:***@
        return re.sub(r"://[^@]+@", "://***:***@", raw)


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.

    Cached after first call; configuration is immutable at runtime.
    Call ``get_settings.cache_clear()`` in tests to reset.
    """
    # Pydantic BaseSettings reads required fields from env/dotenv at runtime.
    # mypy cannot statically verify env-sourced required fields — suppress.
    return Settings()  # type: ignore[call-arg]
