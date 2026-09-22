"""
Clarification Question domain models.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from enum import StrEnum


class QuestionStatus(StrEnum):
    """Lifecycle status of a ClarificationQuestion."""

    PENDING = "PENDING"
    SENT = "SENT"
    ANSWERED = "ANSWERED"
    SKIPPED = "SKIPPED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class ClarificationQuestion:
    """
    A generated question bounded by a specific missing checklist requirement.
    """

    question_id: uuid.UUID
    case_id: uuid.UUID
    evaluation_run_id: uuid.UUID
    requirement_key: str
    missing_item_id: uuid.UUID
    question_text: str
    round_number: int
    status: QuestionStatus
    generator_version: str
    created_at: datetime.datetime
