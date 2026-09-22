"""
Processing status enum.
"""

from enum import StrEnum


class ProcessingStatus(StrEnum):
    """Lifecycle states for a processing run."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
