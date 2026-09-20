"""
Evidence lifecycle states.
"""

from enum import StrEnum


class EvidenceState(StrEnum):
    """Lifecycle states for Evidence."""

    PENDING_UPLOAD = "PENDING_UPLOAD"
    STORED = "STORED"
    QUARANTINED = "QUARANTINED"
    READY = "READY"
    DELETE_PENDING = "DELETE_PENDING"
    DELETED = "DELETED"
    DELETE_FAILED = "DELETE_FAILED"
    FAILED = "FAILED"
