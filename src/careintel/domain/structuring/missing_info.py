"""
Missing Information domain models.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from enum import StrEnum


class RequirementStatus(StrEnum):
    """Evaluation status of a checklist requirement."""

    SATISFIED = "SATISFIED"
    MISSING = "MISSING"
    UNREADABLE = "UNREADABLE"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class MissingInfoItem:
    """
    Result of evaluating a specific checklist requirement against extraction data.
    """

    item_id: uuid.UUID
    case_id: uuid.UUID
    evaluation_run_id: uuid.UUID
    requirement_key: str
    checklist_version: str
    status: RequirementStatus
    materiality: str
    created_at: datetime.datetime
    evidence_candidates: list[uuid.UUID] = field(default_factory=list)
    resolution: str | None = None
