"""
Case state machine and transitions.
"""

from typing import ClassVar

from careintel.core.errors import InvalidTransitionError
from careintel.domain.case.states import CaseState


class CaseStateMachine:
    """
    Deterministic domain state machine for Cases.
    """

    TERMINAL_STATES = frozenset({CaseState.COMPLETED, CaseState.FAILED})

    _VALID_TRANSITIONS: ClassVar[dict[CaseState, frozenset[CaseState]]] = {
        CaseState.CREATED: frozenset({CaseState.CONSENTED}),
        CaseState.CONSENTED: frozenset({CaseState.INPUT_RECEIVED}),
        CaseState.INPUT_RECEIVED: frozenset({CaseState.PROCESSING}),
        CaseState.PROCESSING: frozenset({CaseState.EXTRACTING}),
        CaseState.EXTRACTING: frozenset({CaseState.NORMALIZING}),
        CaseState.NORMALIZING: frozenset({CaseState.RETRIEVING}),
        CaseState.RETRIEVING: frozenset({CaseState.AI_ANALYSIS}),
        CaseState.AI_ANALYSIS: frozenset({CaseState.SAFETY_CHECK}),
        CaseState.SAFETY_CHECK: frozenset({CaseState.TRIAGE_DRAFT_READY}),
        CaseState.TRIAGE_DRAFT_READY: frozenset({CaseState.REVIEW_PENDING}),
        CaseState.REVIEW_PENDING: frozenset({CaseState.REVIEWED, CaseState.ESCALATED}),
        CaseState.REVIEWED: frozenset({CaseState.REFERRED, CaseState.COMPLETED}),
        CaseState.ESCALATED: frozenset(
            {CaseState.REVIEWED}
        ),  # E.g., resolved escalation goes to REVIEWED
        CaseState.REFERRED: frozenset({CaseState.COMPLETED}),
        # Terminal states have no outbound transitions (except to FAILED, see below)
        CaseState.COMPLETED: frozenset(),
        CaseState.FAILED: frozenset(),
    }

    @classmethod
    def validate_transition(cls, from_state: CaseState | str, to_state: CaseState | str) -> None:
        """
        Validate if the transition from `from_state` to `to_state` is allowed.
        Raises InvalidTransitionError if it is not.
        """
        try:
            current = CaseState(from_state)
            target = CaseState(to_state)
        except ValueError as e:
            raise InvalidTransitionError(f"Invalid state value: {e}") from e

        # Any non-terminal state can transition to FAILED
        if target == CaseState.FAILED and current not in cls.TERMINAL_STATES:
            return

        valid_next = cls._VALID_TRANSITIONS.get(current, frozenset())
        if target not in valid_next:
            raise InvalidTransitionError(f"Transition from {current} to {target} is not allowed.")
