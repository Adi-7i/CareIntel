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

    # Structuring (Phase 6)
    TIMELINE_EVALUATED = "timeline_evaluated"
    CONFLICT_DETECTED = "conflict_detected"
    MISSING_INFO_EVALUATED = "missing_info_evaluated"
    CLARIFICATION_QUESTIONS_GENERATED = "clarification_questions_generated"
    CASE_STRUCTURED = "case_structured"
    STRUCTURING_AUTH_DENIED = "structuring_auth_denied"
    STRUCTURING_CONSENT_DENIED = "structuring_consent_denied"
    STRUCTURING_FAILED = "structuring_failed"
    STRUCTURING_DUPLICATE_SKIPPED = "structuring_duplicate_skipped"

    # Knowledge (Phase 7)
    KNOWLEDGE_CREATED = "knowledge_created"
    KNOWLEDGE_VERSION_CREATED = "knowledge_version_created"
    KNOWLEDGE_PUBLISHED = "knowledge_published"
    KNOWLEDGE_RETIRED = "knowledge_retired"

    # Retrieval + AI (Phase 7)
    RETRIEVAL_EXECUTED = "retrieval_executed"
    AI_RUN_STARTED = "ai_run_started"
    AI_RUN_COMPLETED = "ai_run_completed"
    AI_RUN_FAILED = "ai_run_failed"
    AI_DRAFT_REJECTED = "ai_draft_rejected"
    AI_POLICY_BLOCKED = "ai_policy_blocked"
    AI_DRAFT_REVIEWED = "ai_draft_reviewed"
    AI_AUTH_DENIED = "ai_auth_denied"
    AI_CONSENT_DENIED = "ai_consent_denied"

    # Async Workflow (Phase 8)
    TASK_QUEUED = "task_queued"
    TASK_STARTED = "task_started"
    TASK_SUCCEEDED = "task_succeeded"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    TASK_STALE_RECOVERED = "task_stale_recovered"
    WORKFLOW_ADVANCE_REQUESTED = "workflow_advance_requested"

