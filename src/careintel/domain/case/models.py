"""
Case domain models.
"""

import datetime
import uuid
from dataclasses import dataclass

from careintel.domain.case.states import CaseState


@dataclass(frozen=True)
class CaseAggregate:
    """
    The Case domain aggregate root.
    Immutable at the domain level; mutated by creating a new copy with transitioned state.
    """

    case_id: uuid.UUID
    synthetic_subject_id: uuid.UUID
    facility_id: uuid.UUID | None
    state: CaseState
    version: int
    opened_by: uuid.UUID
    assigned_to: uuid.UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass(frozen=True)
class EncounterSummary:
    """
    Encounter summary associated with a Case.
    """

    encounter_id: uuid.UUID
    case_id: uuid.UUID
    encounter_type: str
    occurred_at: datetime.datetime
    notes: str | None
