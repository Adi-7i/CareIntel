"""
Audit events.
"""

from enum import StrEnum


class AuditEventType(StrEnum):
    """
    Critical security events that must be audited.
    """

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REVOKED = "token_revoked"  # noqa: S105
    AUTH_DENIED = "auth_denied"
    CONSENT_REQUESTED = "consent_requested"
    CONSENT_CAPTURED = "consent_captured"
    CONSENT_WITHDRAWN = "consent_withdrawn"
