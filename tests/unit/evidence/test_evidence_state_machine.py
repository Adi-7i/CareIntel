"""
Tests for Evidence State Machine.
"""

import pytest

from careintel.core.errors import InvalidTransitionError
from careintel.domain.evidence.state_machine import EvidenceStateMachine
from careintel.domain.evidence.states import EvidenceState


def test_valid_transitions() -> None:
    validate = EvidenceStateMachine.validate_transition
    validate(EvidenceState.PENDING_UPLOAD, EvidenceState.STORED)
    validate(EvidenceState.STORED, EvidenceState.QUARANTINED)
    validate(EvidenceState.STORED, EvidenceState.READY)
    validate(EvidenceState.QUARANTINED, EvidenceState.STORED)
    validate(EvidenceState.QUARANTINED, EvidenceState.DELETE_PENDING)
    validate(EvidenceState.READY, EvidenceState.DELETE_PENDING)
    validate(EvidenceState.DELETE_PENDING, EvidenceState.DELETED)
    validate(EvidenceState.DELETE_PENDING, EvidenceState.DELETE_FAILED)
    validate(EvidenceState.DELETE_FAILED, EvidenceState.DELETE_PENDING)


def test_invalid_transitions() -> None:
    with pytest.raises(InvalidTransitionError):
        # Must pass through STORED post-scan
        EvidenceStateMachine.validate_transition(EvidenceState.QUARANTINED, EvidenceState.READY)

    with pytest.raises(InvalidTransitionError):
        # Cannot jump from PENDING directly to READY
        EvidenceStateMachine.validate_transition(EvidenceState.PENDING_UPLOAD, EvidenceState.READY)


def test_terminal_states_cannot_transition() -> None:
    with pytest.raises(InvalidTransitionError):
        EvidenceStateMachine.validate_transition(EvidenceState.DELETED, EvidenceState.STORED)

    with pytest.raises(InvalidTransitionError):
        EvidenceStateMachine.validate_transition(EvidenceState.FAILED, EvidenceState.PENDING_UPLOAD)


def test_any_non_terminal_can_fail() -> None:
    EvidenceStateMachine.validate_transition(EvidenceState.PENDING_UPLOAD, EvidenceState.FAILED)
    EvidenceStateMachine.validate_transition(EvidenceState.STORED, EvidenceState.FAILED)
