"""
Task lifecycle states.
"""

from enum import StrEnum


class AsyncTaskStatus(StrEnum):
    """
    Durable lifecycle states for an async background task.
    """

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
