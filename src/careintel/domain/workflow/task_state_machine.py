"""
Task state machine and transitions.
"""

from typing import ClassVar

from careintel.core.errors import InvalidTransitionError
from careintel.domain.workflow.task_states import AsyncTaskStatus


class TaskStateMachine:
    """
    Deterministic domain state machine for async tasks.
    """

    TERMINAL_STATES = frozenset(
        {AsyncTaskStatus.SUCCEEDED, AsyncTaskStatus.FAILED, AsyncTaskStatus.CANCELLED}
    )

    _VALID_TRANSITIONS: ClassVar[dict[AsyncTaskStatus, frozenset[AsyncTaskStatus]]] = {
        AsyncTaskStatus.PENDING: frozenset(
            {
                AsyncTaskStatus.QUEUED,
                AsyncTaskStatus.CANCELLED,
            }
        ),
        AsyncTaskStatus.QUEUED: frozenset(
            {
                AsyncTaskStatus.RUNNING,
                AsyncTaskStatus.PENDING,  # E.g. recovery from queue failure
                AsyncTaskStatus.CANCELLED,
            }
        ),
        AsyncTaskStatus.RUNNING: frozenset(
            {
                AsyncTaskStatus.SUCCEEDED,
                AsyncTaskStatus.FAILED,
                AsyncTaskStatus.PENDING,  # Stale task recovery -> sweep resets to PENDING
            }
        ),
        AsyncTaskStatus.SUCCEEDED: frozenset(),
        AsyncTaskStatus.FAILED: frozenset(),
        AsyncTaskStatus.CANCELLED: frozenset(),
    }

    @classmethod
    def validate_transition(
        cls, from_state: AsyncTaskStatus | str, to_state: AsyncTaskStatus | str
    ) -> None:
        """
        Validate if the transition from `from_state` to `to_state` is allowed.
        Raises InvalidTransitionError if it is not.
        """
        try:
            current = AsyncTaskStatus(from_state)
            target = AsyncTaskStatus(to_state)
        except ValueError as e:
            raise InvalidTransitionError(f"Invalid state value: {e}") from e

        valid_next = cls._VALID_TRANSITIONS.get(current, frozenset())
        if target not in valid_next:
            raise InvalidTransitionError(f"Transition from {current} to {target} is not allowed.")
