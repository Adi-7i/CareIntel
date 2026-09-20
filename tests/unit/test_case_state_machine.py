"""
Unit tests for the Case state machine.
"""

import pytest

from careintel.core.errors import InvalidTransitionError
from careintel.domain.case.state_machine import CaseStateMachine
from careintel.domain.case.states import CaseState


@pytest.mark.unit
def test_valid_transitions() -> None:
    # Test a sequence of valid transitions
    CaseStateMachine.validate_transition(CaseState.CREATED, CaseState.CONSENTED)
    CaseStateMachine.validate_transition(CaseState.CONSENTED, CaseState.INPUT_RECEIVED)
    CaseStateMachine.validate_transition(CaseState.REVIEW_PENDING, CaseState.REVIEWED)
    CaseStateMachine.validate_transition(CaseState.REVIEW_PENDING, CaseState.ESCALATED)
    CaseStateMachine.validate_transition(CaseState.REFERRED, CaseState.COMPLETED)


@pytest.mark.unit
def test_invalid_transitions() -> None:
    # Skipping states should fail
    with pytest.raises(InvalidTransitionError):
        CaseStateMachine.validate_transition(CaseState.CREATED, CaseState.INPUT_RECEIVED)

    # Backwards transitions (unless specifically allowed like ESCALATED -> REVIEWED) should fail
    with pytest.raises(InvalidTransitionError):
        CaseStateMachine.validate_transition(CaseState.AI_ANALYSIS, CaseState.RETRIEVING)


@pytest.mark.unit
def test_any_state_can_fail() -> None:
    # A non-terminal state can transition to FAILED
    CaseStateMachine.validate_transition(CaseState.CREATED, CaseState.FAILED)
    CaseStateMachine.validate_transition(CaseState.PROCESSING, CaseState.FAILED)
    CaseStateMachine.validate_transition(CaseState.REVIEW_PENDING, CaseState.FAILED)


@pytest.mark.unit
def test_terminal_states_cannot_transition() -> None:
    # FAILED cannot transition to anything
    with pytest.raises(InvalidTransitionError):
        CaseStateMachine.validate_transition(CaseState.FAILED, CaseState.COMPLETED)

    # COMPLETED cannot transition to anything, even FAILED
    with pytest.raises(InvalidTransitionError):
        CaseStateMachine.validate_transition(CaseState.COMPLETED, CaseState.FAILED)
    with pytest.raises(InvalidTransitionError):
        CaseStateMachine.validate_transition(CaseState.COMPLETED, CaseState.REVIEWED)


@pytest.mark.unit
def test_invalid_state_value_raises() -> None:
    # Using a state that doesn't exist
    with pytest.raises(InvalidTransitionError):
        CaseStateMachine.validate_transition(CaseState.CREATED, "NOT_A_REAL_STATE")
