"""
Review state machine.
"""

from typing import ClassVar

from careintel.core.errors import InvalidTransitionError
from careintel.domain.review.states import ReviewQueueStatus


class ReviewStateMachine:
    """
    Deterministic domain state machine for the Review Queue.
    """

    _VALID_TRANSITIONS: ClassVar[dict[ReviewQueueStatus, frozenset[ReviewQueueStatus]]] = {
        ReviewQueueStatus.PENDING_ASSIGNMENT: frozenset({ReviewQueueStatus.ASSIGNED}),
        ReviewQueueStatus.ASSIGNED: frozenset({ReviewQueueStatus.IN_REVIEW}),
        ReviewQueueStatus.IN_REVIEW: frozenset({
            ReviewQueueStatus.CLARIFICATION_PENDING,
            ReviewQueueStatus.REVIEW_COMPLETE,
            ReviewQueueStatus.ESCALATED,
        }),
        ReviewQueueStatus.CLARIFICATION_PENDING: frozenset({ReviewQueueStatus.IN_REVIEW}),
        ReviewQueueStatus.ESCALATED: frozenset({ReviewQueueStatus.IN_REVIEW}),
        ReviewQueueStatus.REVIEW_COMPLETE: frozenset(),
    }

    @classmethod
    def validate_transition(cls, from_state: ReviewQueueStatus | str, to_state: ReviewQueueStatus | str) -> None:
        """
        Validate if the transition from `from_state` to `to_state` is allowed.
        Raises InvalidTransitionError if it is not.
        """
        try:
            current = ReviewQueueStatus(from_state)
            target = ReviewQueueStatus(to_state)
        except ValueError as e:
            raise InvalidTransitionError(f"Invalid state value: {e}") from e

        valid_next = cls._VALID_TRANSITIONS.get(current, frozenset())
        if target not in valid_next:
            raise InvalidTransitionError(f"Transition from {current} to {target} is not allowed.")
