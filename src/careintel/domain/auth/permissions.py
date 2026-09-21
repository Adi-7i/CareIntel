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

    # Evidence
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_WRITE = "evidence:write"

    # Processing
    PROCESSING_READ = "processing:read"
    PROCESSING_WRITE = "processing:write"

    # Structuring
    STRUCTURING_READ = "structuring:read"
    STRUCTURING_WRITE = "structuring:write"
