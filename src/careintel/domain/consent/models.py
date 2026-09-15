"""
Consent domain models.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ConsentContext:
    """The current active consent loaded from the database."""

    id: uuid.UUID
    subject_id: uuid.UUID
    purpose: str
    notice_version: str
    state: str
