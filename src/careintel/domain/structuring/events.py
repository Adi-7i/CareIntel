"""
Timeline Event domain models.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from enum import StrEnum

from careintel.domain.structuring.temporal import TemporalExpression, TemporalRelation


class TimelineEventStatus(StrEnum):
    """Lifecycle status of a TimelineEvent."""

    DRAFT = "DRAFT"
    CONFLICTING = "CONFLICTING"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class TimelineEvent:
    """
    A specific temporal event anchored to extraction evidence.
    """

    event_id: uuid.UUID
    case_id: uuid.UUID
    event_type: str
    source_statement: str
    temporal: TemporalExpression
    ordering_relation: TemporalRelation
    status: TimelineEventStatus
    evidence_id: uuid.UUID
    candidate_id: uuid.UUID
    extraction_run_id: uuid.UUID
    version: int
    created_at: datetime.datetime
    ordering_confidence: float | None = None
