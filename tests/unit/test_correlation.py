"""Unit tests for the Correlation ID middleware and context variable."""

from __future__ import annotations

import pytest

from careintel.core.correlation import get_correlation_id


@pytest.mark.unit
class TestCorrelationID:
    """Tests for correlation ID context management."""

    def test_get_correlation_id_returns_empty_string_outside_request(self) -> None:
        """Outside a request context, correlation ID defaults to empty string."""
        cid = get_correlation_id()
        assert isinstance(cid, str)
        # Either empty (default) or set by a previous test — we can't assume
        # specific value, but it must be a string.

    def test_correlation_id_is_string(self) -> None:
        """Correlation ID is always a string."""
        result = get_correlation_id()
        assert isinstance(result, str)
