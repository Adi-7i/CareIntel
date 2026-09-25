"""
Auth API schemas.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    is_active: bool
    roles: list[str]
    permissions: list[str]

    model_config = ConfigDict(from_attributes=True)
