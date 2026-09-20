"""
Evidence state machine and transitions.
"""

from typing import ClassVar

from careintel.core.errors import InvalidTransitionError
from careintel.domain.evidence.states import EvidenceState


class EvidenceStateMachine:
    """
    Deterministic domain state machine for Evidence.
    """

    TERMINAL_STATES = frozenset({EvidenceState.DELETED, EvidenceState.FAILED})

    _VALID_TRANSITIONS: ClassVar[dict[EvidenceState, frozenset[EvidenceState]]] = {
        EvidenceState.PENDING_UPLOAD: frozenset({EvidenceState.STORED}),
        EvidenceState.STORED: frozenset({EvidenceState.QUARANTINED, EvidenceState.READY}),
        EvidenceState.QUARANTINED: frozenset({EvidenceState.STORED, EvidenceState.DELETE_PENDING}),
        EvidenceState.READY: frozenset({EvidenceState.DELETE_PENDING}),
        EvidenceState.DELETE_PENDING: frozenset(
            {EvidenceState.DELETED, EvidenceState.DELETE_FAILED}
        ),
        EvidenceState.DELETE_FAILED: frozenset({EvidenceState.DELETE_PENDING}),
        EvidenceState.DELETED: frozenset(),
        EvidenceState.FAILED: frozenset(),
    }

    @classmethod
    def validate_transition(
        cls, from_state: EvidenceState | str, to_state: EvidenceState | str
    ) -> None:
        """
        Validate if the transition from `from_state` to `to_state` is allowed.
        Raises InvalidTransitionError if it is not.
        """
        try:
            current = EvidenceState(from_state)
            target = EvidenceState(to_state)
        except ValueError as e:
            raise InvalidTransitionError(f"Invalid evidence state value: {e}") from e

        # Any non-terminal state can transition to FAILED
        if target == EvidenceState.FAILED and current not in cls.TERMINAL_STATES:
            return

        valid_next = cls._VALID_TRANSITIONS.get(current, frozenset())
        if target not in valid_next:
            raise InvalidTransitionError(
                f"Transition from {current} to {target} is not allowed for evidence."
            )
