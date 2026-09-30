"""
Request / Correlation ID middleware and context variable.

Each inbound HTTP request is assigned a unique ULID-based correlation ID.
The ID is:
  - Read from the ``X-Correlation-ID`` request header if present (caller-supplied).
  - Generated fresh if absent.
  - Stored in a ContextVar for structured log injection.
  - Echoed back on every response via ``X-Correlation-ID``.

Design decisions:
  - ULID (not UUID4) — time-sortable, URL-safe, 128-bit random space.
  - ContextVar — safe for async; no thread-local leakage.
  - Middleware — applied once at the ASGI boundary; route handlers never touch this.

Usage:
    from careintel.core.correlation import get_correlation_id

    correlation_id = get_correlation_id()  # within a request context
"""

from __future__ import annotations

import contextvars
import re
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from ulid import ULID

from careintel.core.logging import get_logger

CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"
_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

# ContextVar holding the current request's correlation ID.
# Default is an empty string; populated by the middleware before any handler runs.
_correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)
_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
_causation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("causation_id", default="")
_trace_source_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_source", default="application"
)
logger = get_logger(__name__)


def get_correlation_id() -> str:
    """Return the correlation ID for the current request context."""
    return _correlation_id_var.get()


def get_request_id() -> str:
    """Return the current request/execution identifier, when available."""
    return _request_id_var.get()


def get_causation_id() -> str:
    """Return the durable event that caused the current execution, when available."""
    return _causation_id_var.get()


def get_trace_source() -> str:
    """Return the current execution source (api, worker, or application)."""
    return _trace_source_var.get()


def _validated_trace_id(candidate: str | None) -> str:
    """Accept bounded, log-safe caller IDs or generate a fresh identifier."""
    if candidate and _TRACE_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(ULID())


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware: assign/propagate request correlation IDs.

    Applies to every request. Does not read or log the request body.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Prefer caller-supplied ID; fall back to a fresh ULID.
        correlation_id = _validated_trace_id(request.headers.get(CORRELATION_ID_HEADER))
        request_id = _validated_trace_id(request.headers.get(REQUEST_ID_HEADER))

        # Bind to the async context for the lifetime of this request.
        token = _correlation_id_var.set(correlation_id)
        request_token = _request_id_var.set(request_id)
        source_token = _trace_source_var.set("api")
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            # Always reset — prevents context leakage into the next request on
            # connection-keepalive scenarios.
            _correlation_id_var.reset(token)
            _request_id_var.reset(request_token)
            _trace_source_var.reset(source_token)

        # Echo the ID back so callers can correlate client logs with server logs.
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        response.headers[REQUEST_ID_HEADER] = request_id
        route = request.scope.get("route")
        route_template = getattr(route, "path", "unmatched")
        is_health_route = route_template.endswith(("/health/live", "/health/ready"))
        if not is_health_route:
            logger.info(
                "HTTP request completed",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "route": route_template,
                    "status_code": response.status_code,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
        return response
