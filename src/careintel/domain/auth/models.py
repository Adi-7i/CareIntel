"""
Auth domain models.
"""

from __future__ import annotations

import uuid
import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserContext:
    """The current user loaded from the database, attached to the request."""

    id: uuid.UUID
    is_active: bool
    roles: set[str] = field(default_factory=set)
    permissions: set[str] = field(default_factory=set)
    # Map of role_name to facility_id
    role_facilities: dict[str, uuid.UUID | None] = field(default_factory=dict)


@dataclass(frozen=True)
class TokenClaims:
    """Validated claims from a JWT."""

    sub: uuid.UUID
    sid: str
    jti: str
    iss: str
    aud: str
    iat: datetime.datetime | None = None
    exp: datetime.datetime | None = None
