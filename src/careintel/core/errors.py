"""
Global error contract and exception handlers.

Contract
--------
All API error responses share a single envelope:

    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Human-readable description",
            "correlation_id": "01J..."
        }
    }

Design decisions:
- No stack traces, internal paths, or raw exception messages in responses.
- Error codes are machine-readable strings (SCREAMING_SNAKE_CASE).
- HTTP status codes follow RFC 9110; we do NOT invent custom codes.
- A catch-all handler absorbs unexpected exceptions and returns 500.
- All handlers log at the appropriate level (WARNING for 4xx, ERROR for 5xx).

Usage:
    from careintel.core.errors import register_exception_handlers
    register_exception_handlers(app)
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from careintel.core.correlation import get_correlation_id

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Domain / Application exceptions (no FastAPI dependency)
# ──────────────────────────────────────────────────────────────────────────────


class CareIntelError(Exception):
    """Base class for all CareIntel application exceptions."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


class NotFoundError(CareIntelError):
    """Resource not found."""

    code = "NOT_FOUND"
    http_status = 404
    message = "The requested resource was not found."


class ConflictError(CareIntelError):
    """Resource already exists or state conflict."""

    code = "CONFLICT"
    http_status = 409
    message = "A conflict occurred with the current state of the resource."


class ValidationError(CareIntelError):
    """Domain-level validation failure (distinct from Pydantic request validation)."""

    code = "DOMAIN_VALIDATION_ERROR"
    http_status = 422
    message = "The request could not be processed due to a validation error."


class ServiceUnavailableError(CareIntelError):
    """Downstream dependency (e.g. database) is temporarily unavailable."""

    code = "SERVICE_UNAVAILABLE"
    http_status = 503
    message = "A required service is temporarily unavailable. Please try again later."


# ──────────────────────────────────────────────────────────────────────────────
# Response builders
# ──────────────────────────────────────────────────────────────────────────────


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    """Build a standardised error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "correlation_id": get_correlation_id(),
            }
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────────────────


async def _handle_careintel_error(
    request: Request,
    exc: CareIntelError,
) -> JSONResponse:
    """Handle known CareIntel application exceptions."""
    level = logging.WARNING if exc.http_status < 500 else logging.ERROR
    logger.log(
        level,
        "Application exception",
        extra={
            "error_code": exc.code,
            "http_status": exc.http_status,
            "correlation_id": get_correlation_id(),
            "path": request.url.path,
        },
    )
    return _error_response(
        status_code=exc.http_status,
        code=exc.code,
        message=exc.message,
    )


async def _handle_http_exception(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle Starlette / FastAPI HTTP exceptions (e.g. 404, 405)."""
    # Map numeric status to a machine-readable code using stdlib HTTP status names
    try:
        phrase = HTTPStatus(exc.status_code).phrase.upper().replace(" ", "_")
    except ValueError:
        phrase = "HTTP_ERROR"

    logger.warning(
        "HTTP exception",
        extra={
            "http_status": exc.status_code,
            "detail": str(exc.detail),
            "correlation_id": get_correlation_id(),
            "path": request.url.path,
        },
    )
    return _error_response(
        status_code=exc.status_code,
        code=phrase,
        message=str(exc.detail) if exc.detail else phrase,
    )


async def _handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic request validation errors (422)."""
    # Summarise errors without echoing raw user input (privacy)
    error_count = len(exc.errors())
    logger.warning(
        "Request validation failed",
        extra={
            "error_count": error_count,
            "correlation_id": get_correlation_id(),
            "path": request.url.path,
        },
    )
    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message=f"Request validation failed with {error_count} error(s). "
        "Check request parameters and body.",
    )


async def _handle_unhandled_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for unexpected exceptions."""
    logger.exception(
        "Unhandled exception",
        extra={
            "exc_type": type(exc).__name__,
            "correlation_id": get_correlation_id(),
            "path": request.url.path,
        },
    )
    return _error_response(
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again or contact support.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI application.

    Call this once during application composition in main.py.
    Order matters: more specific types must be registered before broader ones.
    """
    # Known application errors
    app.add_exception_handler(
        CareIntelError,
        _handle_careintel_error,  # type: ignore[arg-type]
    )
    # FastAPI/Starlette HTTP exceptions
    app.add_exception_handler(
        StarletteHTTPException,
        _handle_http_exception,  # type: ignore[arg-type]
    )
    # Pydantic request validation
    app.add_exception_handler(
        RequestValidationError,
        _handle_validation_error,  # type: ignore[arg-type]
    )
    # Catch-all (must be last)
    app.add_exception_handler(
        Exception,
        _handle_unhandled_exception,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Public type alias for handler typing
# ──────────────────────────────────────────────────────────────────────────────
ErrorDetail = dict[str, Any]
