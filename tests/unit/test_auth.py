"""
Auth and security unit tests.
"""

from __future__ import annotations

import uuid

import pytest

from careintel.application.auth.password_hasher import PasswordHasher
from careintel.application.auth.token_service import JWTService
from careintel.core.config import get_settings
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy


@pytest.mark.unit
def test_password_hasher() -> None:
    hasher = PasswordHasher()
    password = "SuperSecretPassword123"
    hashed = hasher.hash(password)

    assert hashed != password
    assert hasher.verify(password, hashed) is True
    assert hasher.verify("wrongpassword", hashed) is False


@pytest.mark.unit
def test_authorization_policy_deny_default() -> None:
    user = UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"patient"},
        permissions=set(),
    )
    # No permissions, should deny
    granted = AuthorizationPolicy.evaluate(user, Permission.CONSENT_READ)
    assert granted is False


@pytest.mark.unit
def test_authorization_policy_inactive_user() -> None:
    user = UserContext(
        id=uuid.uuid4(),
        is_active=False,
        roles={"admin"},
        permissions={Permission.MANAGE_SYSTEM.value},
    )
    # Inactive user should be denied even with permissions
    granted = AuthorizationPolicy.evaluate(user, Permission.MANAGE_SYSTEM)
    assert granted is False


@pytest.mark.unit
def test_authorization_policy_granted() -> None:
    user = UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"admin"},
        permissions={Permission.MANAGE_SYSTEM.value},
    )
    granted = AuthorizationPolicy.evaluate(user, Permission.MANAGE_SYSTEM)
    assert granted is True


@pytest.mark.unit
def test_authorization_policy_facility_scope_system_admin() -> None:
    user = UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"admin"},
        permissions={Permission.CASE_READ.value},
        role_facilities={"admin": None},  # System-wide
    )
    facility_id = uuid.uuid4()
    granted = AuthorizationPolicy.evaluate(user, Permission.CASE_READ, facility_scope=facility_id)
    assert granted is True


@pytest.mark.unit
def test_authorization_policy_facility_scope_mismatch() -> None:
    assigned_facility = uuid.uuid4()
    other_facility = uuid.uuid4()

    user = UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"doctor"},
        permissions={Permission.CASE_READ.value},
        role_facilities={"doctor": assigned_facility},
    )

    # Should deny access to other facility
    granted = AuthorizationPolicy.evaluate(
        user, Permission.CASE_READ, facility_scope=other_facility
    )
    assert granted is False


@pytest.mark.unit
def test_authorization_policy_missing_scope_mapping_denied() -> None:
    user = UserContext(
        id=uuid.uuid4(),
        is_active=True,
        roles={"doctor"},
        permissions={Permission.CASE_READ.value},
        role_facilities={},
    )

    granted = AuthorizationPolicy.evaluate(
        user,
        Permission.CASE_READ,
        facility_scope=uuid.uuid4(),
    )

    assert granted is False


@pytest.mark.unit
def test_jwt_round_trip_preserves_required_session_timestamps() -> None:
    service = JWTService(get_settings())
    token = service.issue_token(uuid.uuid4(), uuid.uuid4())

    claims = service.validate_token(token)

    assert claims.iat is not None
    assert claims.exp is not None
    assert claims.exp > claims.iat
