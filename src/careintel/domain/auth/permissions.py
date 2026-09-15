"""
Permission definitions.
"""

from enum import StrEnum


class Permission(StrEnum):
    """System permissions."""

    # Admin
    MANAGE_USERS = "manage:users"
    MANAGE_SYSTEM = "manage:system"

    # Consent
    CONSENT_READ = "consent:read"
    CONSENT_WRITE = "consent:write"

    # Future Case Management placeholder
    CASE_READ = "case:read"
    CASE_WRITE = "case:write"
