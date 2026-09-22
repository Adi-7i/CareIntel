"""
Structured JSON logging with sensitive-data protection.

Design decisions:
- JSON format in all non-development environments for log aggregation.
- A SensitiveDataFilter scrubs known sensitive field names from log records.
- Request body is NEVER logged (enforced at middleware level, not here).
- Log level is driven by settings.

Usage:
    from careintel.core.logging import configure_logging, get_logger

    configure_logging(settings)
    logger = get_logger(__name__)
    logger.info("Something happened", extra={"correlation_id": "..."})
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from pythonjsonlogger.json import JsonFormatter

if TYPE_CHECKING:
    from careintel.core.config import Settings


# ──────────────────────────────────────────────────────────────────────────────
# Sensitive field names — values for these keys are redacted in log output.
# Extend this set as new integration points are added.
# ──────────────────────────────────────────────────────────────────────────────
_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "secret_key",
        "api_key",
        "apikey",
        "key",
        "authorization",
        "auth",
        "cookie",
        "session",
        "dsn",
        "database_url",
        "connection_string",
        "private_key",
        "client_secret",
        "bearer",
    }
)

_REDACTED = "[REDACTED]"


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that redacts sensitive values from LogRecord extra fields.

    Operates on the record's __dict__ to catch all extra= keyword arguments
    passed to logger calls. Case-insensitive key matching.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        for key in list(record.__dict__.keys()):
            if key.lower() in _SENSITIVE_KEYS:
                setattr(record, key, _REDACTED)
        return True


class _CareIntelJsonFormatter(JsonFormatter):
    """
    JSON formatter that adds standard fields to every log record.

    Added fields: service, environment, level.
    All other fields come from the record and its extras.
    """

    def add_fields(
        self,
        log_data: dict[str, object],
        record: logging.LogRecord,
        message_dict: dict[str, object],
    ) -> None:
        super().add_fields(log_data, record, message_dict)
        log_data["level"] = record.levelname


def configure_logging(settings: Settings) -> None:
    """
    Configure root logger and careintel logger.

    - JSON format everywhere (human-readable in development too; parse-friendly).
    - SensitiveDataFilter applied globally.
    - SQLAlchemy engine logs gated to WARNING unless echo_sql is on.

    Call once at application startup before any other code logs.
    """
    formatter = _CareIntelJsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "name": "logger"},
        static_fields={
            "service": "careintel",
            "env": settings.app_env.value,
        },
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    sensitive_filter = SensitiveDataFilter()
    handler.addFilter(sensitive_filter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.app_log_level.value)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo_sql else logging.WARNING
    )

    logger = get_logger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": settings.app_log_level.value,
            "env": settings.app_env.value,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Use ``__name__`` as convention."""
    return logging.getLogger(name)
