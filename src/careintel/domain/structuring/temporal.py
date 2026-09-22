"""
Temporal domain models for the Structuring Engine.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from enum import StrEnum


class TemporalPrecision(StrEnum):
    """Precision level of a temporal expression."""

    EXACT = "EXACT"
    DATE = "DATE"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"
    RELATIVE = "RELATIVE"
    DURATION = "DURATION"
    UNKNOWN = "UNKNOWN"


class TemporalResolutionState(StrEnum):
    """Resolution state of a temporal expression."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    MISSING = "MISSING"


class TemporalRelation(StrEnum):
    """Ordering relationship between temporal events."""

    BEFORE = "BEFORE"
    AFTER = "AFTER"
    OVERLAPS = "OVERLAPS"
    DURING = "DURING"
    SIMULTANEOUS = "SIMULTANEOUS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TemporalExpression:
    """
    Representation of a temporal reference in evidence.

    Critical invariant: normalized_start and normalized_end must ONLY
    be populated if resolution_state is RESOLVED.
    """

    raw_text: str
    precision: TemporalPrecision
    resolution_state: TemporalResolutionState
    normalized_start: datetime.date | None = None
    normalized_end: datetime.date | None = None
    anchor_description: str | None = None
    anchor_evidence_id: uuid.UUID | None = None
    unresolved_reason: str | None = None

    def __post_init__(self) -> None:
        if self.resolution_state != TemporalResolutionState.RESOLVED:
            if self.normalized_start is not None or self.normalized_end is not None:
                raise ValueError(
                    "normalized dates cannot be set unless resolution_state is RESOLVED"
                )
