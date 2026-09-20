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

    # Evidence
    EVIDENCE_TEXT_CREATED = "evidence_text_created"
    EVIDENCE_UPLOAD_STARTED = "evidence_upload_started"
    EVIDENCE_UPLOAD_ACCEPTED = "evidence_upload_accepted"
    EVIDENCE_UPLOAD_REJECTED = "evidence_upload_rejected"
    EVIDENCE_STATE_TRANSITION = "evidence_state_transition"
    EVIDENCE_DOWNLOAD_AUTHORIZED = "evidence_download_authorized"
    EVIDENCE_DUPLICATE_DETECTED = "evidence_duplicate_detected"
    EVIDENCE_AUTH_DENIED = "evidence_auth_denied"
    EVIDENCE_VALIDATION_FAILED = "evidence_validation_failed"
    EVIDENCE_STORAGE_FAILURE = "evidence_storage_failure"
    EVIDENCE_CONSENT_DENIED = "evidence_consent_denied"

    # Processing (Phase 5)
    PROCESSING_REQUESTED = "processing_requested"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"
    PROCESSING_AUTH_DENIED = "processing_auth_denied"
    PROCESSING_CONSENT_DENIED = "processing_consent_denied"
    PROCESSING_DUPLICATE_SKIPPED = "processing_duplicate_skipped"
