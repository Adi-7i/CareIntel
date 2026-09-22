"""
Unit tests for TemporalNormalizer.
"""

import datetime

from careintel.application.structuring.temporal_normalizer import TemporalNormalizer
from careintel.domain.structuring.temporal import (
    TemporalPrecision,
    TemporalResolutionState,
)


def test_exact_iso_date_resolves() -> None:
    expr = TemporalNormalizer.normalize("2025-10-15")
    assert expr.resolution_state == TemporalResolutionState.RESOLVED
    assert expr.precision == TemporalPrecision.DATE
    assert expr.normalized_start == datetime.date(2025, 10, 15)
    assert expr.normalized_end == datetime.date(2025, 10, 15)
    assert expr.raw_text == "2025-10-15"


def test_relative_date_with_anchor_resolves() -> None:
    anchor = datetime.date(2025, 10, 15)
    expr = TemporalNormalizer.normalize("yesterday", anchor_date=anchor)
    assert expr.resolution_state == TemporalResolutionState.RESOLVED
    assert expr.precision == TemporalPrecision.RELATIVE
    assert expr.normalized_start == datetime.date(2025, 10, 14)
    assert expr.normalized_end == datetime.date(2025, 10, 14)


def test_relative_date_without_anchor_unresolved() -> None:
    expr = TemporalNormalizer.normalize("yesterday", anchor_date=None)
    assert expr.resolution_state == TemporalResolutionState.UNRESOLVED
    assert expr.precision == TemporalPrecision.RELATIVE
    assert expr.normalized_start is None
    assert expr.normalized_end is None
    assert "lacks explicit anchor" in str(expr.unresolved_reason)
    assert expr.raw_text == "yesterday"


def test_duration_remains_unresolved() -> None:
    expr = TemporalNormalizer.normalize("since childhood")
    assert expr.resolution_state == TemporalResolutionState.UNRESOLVED
    assert expr.precision == TemporalPrecision.DURATION
    assert expr.normalized_start is None


def test_unknown_format_remains_unresolved() -> None:
    expr = TemporalNormalizer.normalize("some random time")
    assert expr.resolution_state == TemporalResolutionState.UNRESOLVED
    assert expr.precision == TemporalPrecision.UNKNOWN
    assert expr.normalized_start is None


def test_empty_string_missing() -> None:
    expr = TemporalNormalizer.normalize("   ")
    assert expr.resolution_state == TemporalResolutionState.MISSING
    assert expr.precision == TemporalPrecision.UNKNOWN
    assert expr.normalized_start is None
