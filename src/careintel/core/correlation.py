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
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from ulid import ULID

CORRELATION_ID_HEADER = "X-Correlation-ID"

# ContextVar holding the current request's correlation ID.
# Default is an empty string; populated by the middleware before any handler runs.
_correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


def get_correlation_id() -> str:
    """Return the correlation ID for the current request context."""
    return _correlation_id_var.get()


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
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(ULID())

        # Bind to the async context for the lifetime of this request.
        token = _correlation_id_var.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            # Always reset — prevents context leakage into the next request on
            # connection-keepalive scenarios.
            _correlation_id_var.reset(token)

        # Echo the ID back so callers can correlate client logs with server logs.
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
