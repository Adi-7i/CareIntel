from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class PrepareReferralRequest(BaseModel):
    evidence_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)


class ReferralPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    version: int
    prepared_by: uuid.UUID
    evidence_ids: list[str]
    status: str


class InitiateHandoffRequest(BaseModel):
    recipient_id: uuid.UUID


class SendHandoffRequest(BaseModel):
    expected_version: int = Field(ge=1)


class AcknowledgeHandoffRequest(BaseModel):
    reference: str = Field(min_length=1, max_length=500)
    expected_version: int = Field(ge=1)


class CompleteHandoffRequest(BaseModel):
    expected_handoff_version: int = Field(ge=1)
    expected_case_version: int = Field(ge=1)


class HandoffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    referral_package_id: uuid.UUID
    recipient_id: uuid.UUID
    channel: str | None
    status: str
    sent_by: uuid.UUID
    sent_at: datetime.datetime | None
    acknowledged_at: datetime.datetime | None
    version: int


class RecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    recipient_type: str
