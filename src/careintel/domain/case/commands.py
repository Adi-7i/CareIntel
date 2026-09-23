"""
Case commands.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from careintel.domain.case.states import CaseState


@dataclass
class CreateCaseCommand:
    synthetic_subject_id: uuid.UUID
    facility_id: uuid.UUID | None
    opened_by: uuid.UUID
    correlation_id: str


@dataclass
class TransitionCaseCommand:
    case_id: uuid.UUID
    actor_id: uuid.UUID
    from_state: CaseState | str
    to_state: CaseState | str
    expected_version: int
    reason: str | None
    correlation_id: str


@dataclass(frozen=True)
class CreateEncounterCommand:
    case_id: uuid.UUID
    encounter_type: str
    occurred_at: datetime
    notes: str | None
    actor_id: uuid.UUID
    correlation_id: str
