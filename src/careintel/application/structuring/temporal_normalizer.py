"""
Temporal normalization logic.
"""

from __future__ import annotations

import datetime
from typing import ClassVar

from careintel.domain.structuring.temporal import (
    TemporalExpression,
    TemporalPrecision,
    TemporalResolutionState,
)


class TemporalNormalizer:
    """
    Normalizes raw temporal expressions extracted from evidence.

    Critical invariant: relative expressions are only resolved if a valid,
    explicit anchor date is provided. No defaults (like evidence.created_at)
    are automatically assumed.
    """

    # Static keywords for demo parsing. A real system would use NLP.
    _RELATIVE_KEYWORDS: ClassVar[set[str]] = {
        "ago",
        "last",
        "yesterday",
        "tomorrow",
        "today",
        "next",
        "since",
        "for",
    }

    @staticmethod
    def normalize(raw_text: str, anchor_date: datetime.date | None = None) -> TemporalExpression:
        """
        Attempt to normalize a raw temporal string.
        """
        text = raw_text.strip().lower()

        if not text:
            return TemporalExpression(
                raw_text=raw_text,
                precision=TemporalPrecision.UNKNOWN,
                resolution_state=TemporalResolutionState.MISSING,
                unresolved_reason="Empty expression",
            )

        # 1. Check for exact ISO dates (YYYY-MM-DD)
        if len(text) == 10 and text.count("-") == 2:
            try:
                date_val = datetime.date.fromisoformat(text)
                return TemporalExpression(
                    raw_text=raw_text,
                    precision=TemporalPrecision.DATE,
                    resolution_state=TemporalResolutionState.RESOLVED,
                    normalized_start=date_val,
                    normalized_end=date_val,
                )
            except ValueError:
                pass  # Fall through

        # 2. Check for "duration" indicators (since, for)
        if text.startswith("since") or text.startswith("for "):
            return TemporalExpression(
                raw_text=raw_text,
                precision=TemporalPrecision.DURATION,
                resolution_state=TemporalResolutionState.UNRESOLVED,
                unresolved_reason="Durations require contextual bounds",
            )

        # 3. Check for relative expressions
        is_relative = any(kw in text for kw in TemporalNormalizer._RELATIVE_KEYWORDS)
        if is_relative:
            if not anchor_date:
                return TemporalExpression(
                    raw_text=raw_text,
                    precision=TemporalPrecision.RELATIVE,
                    resolution_state=TemporalResolutionState.UNRESOLVED,
                    unresolved_reason="Relative expression lacks explicit anchor",
                )

            # Very naive resolution for prototype rules
            resolved_date = None
            if "yesterday" in text:
                resolved_date = anchor_date - datetime.timedelta(days=1)
            elif "today" in text:
                resolved_date = anchor_date
            elif "tomorrow" in text:
                resolved_date = anchor_date + datetime.timedelta(days=1)
            elif "3 days ago" in text:
                resolved_date = anchor_date - datetime.timedelta(days=3)

            if resolved_date:
                return TemporalExpression(
                    raw_text=raw_text,
                    precision=TemporalPrecision.RELATIVE,
                    resolution_state=TemporalResolutionState.RESOLVED,
                    normalized_start=resolved_date,
                    normalized_end=resolved_date,
                    anchor_description="explicit",
                )

            return TemporalExpression(
                raw_text=raw_text,
                precision=TemporalPrecision.RELATIVE,
                resolution_state=TemporalResolutionState.UNRESOLVED,
                unresolved_reason="Unsupported relative pattern",
            )

        # 4. Unknown/unsupported expression
        return TemporalExpression(
            raw_text=raw_text,
            precision=TemporalPrecision.UNKNOWN,
            resolution_state=TemporalResolutionState.UNRESOLVED,
            unresolved_reason="Unrecognized temporal format",
        )
