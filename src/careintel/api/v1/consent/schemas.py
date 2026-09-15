"""
Consent API schemas.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class ConsentRequest(BaseModel):
    subject_id: uuid.UUID
    purpose: str
    notice_version: str


class ConsentResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    purpose: str
    notice_version: str
    state: str

    model_config = ConfigDict(from_attributes=True)
