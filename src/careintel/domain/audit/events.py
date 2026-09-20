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
    CASE_CREATED = "case_created"
    CASE_STATE_TRANSITION = "case_state_transition"
    CASE_INVALID_TRANSITION = "case_invalid_transition"
    CASE_AUTH_DENIED = "case_auth_denied"
    CASE_CONCURRENCY_CONFLICT = "case_concurrency_conflict"
    CASE_CONSENT_DENIED = "case_consent_denied"
