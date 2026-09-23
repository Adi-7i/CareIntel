"""
Case schemas.
"""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from careintel.domain.case.states import CaseState


class CreateCaseRequest(BaseModel):
    synthetic_subject_id: uuid.UUID = Field(..., description="Synthetic patient UUID")
    facility_id: uuid.UUID | None = Field(None, description="Optional facility boundary")
    consent_id: uuid.UUID = Field(..., description="Active consent ID authorizing this case")


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: uuid.UUID
    synthetic_subject_id: uuid.UUID
    facility_id: uuid.UUID | None
    state: CaseState
    version: int
    opened_by: uuid.UUID
    assigned_to: uuid.UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class TransitionRequest(BaseModel):
    to_state: CaseState = Field(..., description="The state to transition to")
    expected_version: int = Field(
        ..., description="Current version of the case aggregate (optimistic lock)"
    )
    reason: str | None = Field(None, description="Optional reason for transition")


class CaseStateHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_state: str
    to_state: str
    actor_id: uuid.UUID
    aggregate_version: int
    transitioned_at: datetime.datetime
    reason: str | None


class CaseHistoryResponse(BaseModel):
    case_id: uuid.UUID
    history: list[CaseStateHistoryEntry]


class CreateEncounterRequest(BaseModel):
    encounter_type: str = Field(min_length=1, max_length=100)
    occurred_at: datetime.datetime
    notes: str | None = Field(default=None, max_length=2000)


class EncounterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    encounter_id: uuid.UUID
    case_id: uuid.UUID
    encounter_type: str
    occurred_at: datetime.datetime
    notes: str | None


class EncounterListResponse(BaseModel):
    case_id: uuid.UUID
    encounters: list[EncounterResponse]
