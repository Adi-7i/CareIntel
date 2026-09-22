"""
Conflict domain models.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum


class ConflictStatus(StrEnum):
    """Lifecycle status of a ConflictRecord."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"


@dataclass(frozen=True)
class ConflictRecord:
    """
    Represents a detected conflict between multiple extracted candidates
    for the same logical field type.
    """

    conflict_id: uuid.UUID
    case_id: uuid.UUID
    field_type: str
    candidate_ids: list[uuid.UUID]
    status: ConflictStatus
    detection_run_id: uuid.UUID
