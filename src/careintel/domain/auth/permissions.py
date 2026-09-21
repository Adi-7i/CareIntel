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

    # Knowledge (Phase 7)
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"

    # AI (Phase 7)
    AI_READ = "ai:read"
    AI_WRITE = "ai:write"

    # Review (Phase 9)
    REVIEW_READ = "review:read"
    REVIEW_WRITE = "review:write"
    REVIEW_ASSIGN = "review:assign"

    # Escalation (Phase 9)
    ESCALATION_READ = "escalation:read"
    ESCALATION_WRITE = "escalation:write"

    # Referral / Handoff (Phase 9)
    REFERRAL_READ = "referral:read"
    REFERRAL_WRITE = "referral:write"
    HANDOFF_READ = "handoff:read"
    HANDOFF_WRITE = "handoff:write"

    # Recipient management (Phase 9)
    RECIPIENT_MANAGE = "recipient:manage"
