"""
Review states and enums.
"""

from enum import StrEnum


class ReviewQueueStatus(StrEnum):
    PENDING_ASSIGNMENT = "PENDING_ASSIGNMENT"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    CLARIFICATION_PENDING = "CLARIFICATION_PENDING"
    REVIEW_COMPLETE = "REVIEW_COMPLETE"
    ESCALATED = "ESCALATED"


class ReviewDecisionType(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    ESCALATE = "ESCALATE"
    REFER = "REFER"


class DraftAction(StrEnum):
    ACCEPT = "ACCEPT"
    EDIT = "EDIT"
    REJECT = "REJECT"


class EscalationStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
