"""
Handoff state machine.
"""

from typing import ClassVar

from careintel.core.errors import InvalidTransitionError
from careintel.domain.handoff.states import HandoffStatus


class HandoffStateMachine:
    """
    Deterministic domain state machine for Handoff delivery.
    """

    _VALID_TRANSITIONS: ClassVar[dict[HandoffStatus, frozenset[HandoffStatus]]] = {
        HandoffStatus.DRAFT: frozenset({HandoffStatus.READY, HandoffStatus.CANCELLED}),
        HandoffStatus.READY: frozenset({HandoffStatus.SENDING, HandoffStatus.CANCELLED}),
        HandoffStatus.SENDING: frozenset({
            HandoffStatus.SENT,
            HandoffStatus.DELIVERY_FAILED,
        }),
        HandoffStatus.SENT: frozenset({
            HandoffStatus.ACKNOWLEDGEMENT_PENDING,
            HandoffStatus.ACKNOWLEDGED,
            HandoffStatus.DELIVERY_FAILED, # Can happen if async receipt processing fails
        }),
        HandoffStatus.DELIVERY_FAILED: frozenset({
            HandoffStatus.READY, # Retry
            HandoffStatus.CANCELLED,
        }),
        HandoffStatus.ACKNOWLEDGEMENT_PENDING: frozenset({
            HandoffStatus.ACKNOWLEDGED,
            HandoffStatus.DELIVERY_FAILED,
        }),
        HandoffStatus.ACKNOWLEDGED: frozenset({HandoffStatus.COMPLETED}),
        HandoffStatus.COMPLETED: frozenset(),
        HandoffStatus.CANCELLED: frozenset(),
    }

    @classmethod
    def validate_transition(cls, from_state: HandoffStatus | str, to_state: HandoffStatus | str) -> None:
        """
        Validate if the transition from `from_state` to `to_state` is allowed.
        Raises InvalidTransitionError if it is not.
        """
        try:
            current = HandoffStatus(from_state)
            target = HandoffStatus(to_state)
        except ValueError as e:
            raise InvalidTransitionError(f"Invalid state value: {e}") from e

        valid_next = cls._VALID_TRANSITIONS.get(current, frozenset())
        if target not in valid_next:
            raise InvalidTransitionError(f"Transition from {current} to {target} is not allowed.")
