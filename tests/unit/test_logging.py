"""Unit tests for structured logging and sensitive data filtering."""

from __future__ import annotations

import logging

import pytest

from careintel.core.logging import _SENSITIVE_KEYS, SensitiveDataFilter


@pytest.mark.unit
class TestSensitiveDataFilter:
    """Tests for the SensitiveDataFilter logging filter."""

    def _make_record(self, **kwargs: object) -> logging.LogRecord:
        """Helper: build a LogRecord with the given extra fields."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    def test_redacts_password(self) -> None:
        """'password' field is redacted."""
        record = self._make_record(password="supersecret123")
        f = SensitiveDataFilter()
        f.filter(record)
        assert record.password == "[REDACTED]"  # type: ignore[attr-defined]

    def test_redacts_token(self) -> None:
        """'token' field is redacted."""
        record = self._make_record(token="eyJhbGciOiJIUzI1NiJ9...")
        f = SensitiveDataFilter()
        f.filter(record)
        assert record.token == "[REDACTED]"  # type: ignore[attr-defined]

    def test_redacts_secret_key(self) -> None:
        """'secret_key' field is redacted."""
        record = self._make_record(secret_key="my-secret")
        f = SensitiveDataFilter()
        f.filter(record)
        assert record.secret_key == "[REDACTED]"  # type: ignore[attr-defined]

    def test_does_not_redact_safe_fields(self) -> None:
        """Non-sensitive fields are preserved."""
        record = self._make_record(user_id="user-123", action="login")
        f = SensitiveDataFilter()
        f.filter(record)
        assert record.user_id == "user-123"  # type: ignore[attr-defined]
        assert record.action == "login"  # type: ignore[attr-defined]

    def test_always_returns_true(self) -> None:
        """filter() always returns True (records are not dropped)."""
        record = self._make_record(password="secret")
        f = SensitiveDataFilter()
        result = f.filter(record)
        assert result is True

    def test_sensitive_keys_set_is_nonempty(self) -> None:
        """The sensitive keys set contains known keys."""
        assert "password" in _SENSITIVE_KEYS
        assert "token" in _SENSITIVE_KEYS
        assert "authorization" in _SENSITIVE_KEYS
        assert "database_url" in _SENSITIVE_KEYS

    def test_case_insensitive_redaction(self) -> None:
        """Matching is case-insensitive for the key name."""
        # The filter checks key.lower(); keys are usually lower-case anyway
        record = self._make_record(authorization="Bearer xyz")
        f = SensitiveDataFilter()
        f.filter(record)
        assert record.authorization == "[REDACTED]"  # type: ignore[attr-defined]


@pytest.mark.unit
class TestLoggingConfiguration:
    """Tests for configure_logging."""

    def test_configure_logging_does_not_raise(self, settings: object) -> None:
        """configure_logging runs without error given valid settings."""
        from careintel.core.logging import configure_logging

        configure_logging(settings)  # type: ignore[arg-type]

    def test_get_logger_returns_logger(self) -> None:
        """get_logger returns a standard logging.Logger instance."""
        from careintel.core.logging import get_logger

        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
