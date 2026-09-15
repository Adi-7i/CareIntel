"""Unit tests for the global error contract and exception hierarchy."""

from __future__ import annotations

import pytest

from careintel.core.errors import (
    CareIntelError,
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)


@pytest.mark.unit
class TestExceptionHierarchy:
    """Tests for the domain exception class hierarchy."""

    def test_all_exceptions_are_careintel_errors(self) -> None:
        """All domain errors inherit from CareIntelError."""
        assert issubclass(NotFoundError, CareIntelError)
        assert issubclass(ConflictError, CareIntelError)
        assert issubclass(ValidationError, CareIntelError)
        assert issubclass(ServiceUnavailableError, CareIntelError)

    def test_not_found_error_attributes(self) -> None:
        """NotFoundError has correct HTTP status and code."""
        err = NotFoundError()
        assert err.http_status == 404
        assert err.code == "NOT_FOUND"

    def test_conflict_error_attributes(self) -> None:
        """ConflictError has correct HTTP status and code."""
        err = ConflictError()
        assert err.http_status == 409
        assert err.code == "CONFLICT"

    def test_validation_error_attributes(self) -> None:
        """Domain ValidationError has correct HTTP status and code."""
        err = ValidationError()
        assert err.http_status == 422
        assert err.code == "DOMAIN_VALIDATION_ERROR"

    def test_service_unavailable_error_attributes(self) -> None:
        """ServiceUnavailableError has correct HTTP status and code."""
        err = ServiceUnavailableError()
        assert err.http_status == 503
        assert err.code == "SERVICE_UNAVAILABLE"

    def test_custom_message_overrides_default(self) -> None:
        """Custom message passed to constructor overrides class-level default."""
        err = NotFoundError("Patient record not found")
        assert err.message == "Patient record not found"
        assert str(err) == "Patient record not found"

    def test_no_fastapi_dependency(self) -> None:
        """CareIntelError and subclasses do not import FastAPI internals."""
        import inspect

        import careintel.core.errors as errors_module

        source = inspect.getsource(errors_module)
        # The exception *classes* should not depend on fastapi; handlers may.
        # We check that the import of fastapi is only for handlers, not for the
        # exception classes themselves by checking the class definitions don't
        # reference FastAPI-specific base classes.
        assert "CareIntelError(Exception)" in source
        assert "CareIntelError(FastAPI" not in source
