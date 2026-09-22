"""
Unit tests for the Deterministic AI Safety Policy Service.
"""

import uuid

from careintel.application.ai.policy_service import PolicyService
from careintel.domain.ai.models import AIDraft, ClaimProvenance, ContextPassage, SafeContext
from careintel.domain.ai.status import (
    ContentOrigin,
    DraftReviewerStatus,
    PolicyOutcome,
    ValidationStatus,
)


def test_provenance_integrity_rule_passes() -> None:
    # Setup context with valid source IDs
    valid_id1 = uuid.uuid4()
    valid_id2 = uuid.uuid4()
    context = SafeContext(
        system_instructions="",
        task_instructions="",
        output_schema={},
        policy_constraints=[],
        knowledge_passages=[
            ContextPassage(
                content="fact 1",
                origin=ContentOrigin.KNOWLEDGE,
                source_id=valid_id1,
                citation_locator=None,
            )
        ],
        patient_evidence=[
            ContextPassage(
                content="fact 2",
                origin=ContentOrigin.PATIENT_TEXT,
                source_id=valid_id2,
                citation_locator=None,
            )
        ],
        stt_transcripts=[],
        ocr_content=[],
        extracted_facts=[],
        timeline_events=[],
        missing_information=[],
        conflicting_information=[],
        retrieval_metadata=None,
    )

    # Setup draft citing the valid source IDs
    draft = AIDraft(
        draft_id=uuid.uuid4(),
        ai_run_id=uuid.uuid4(),
        content={},
        validation_status=ValidationStatus.ACCEPTED,
        validation_errors=[],
        claim_provenance=[
            ClaimProvenance(
                claim_text="xyz", status="SUPPORTED", supporting_source_ids=[valid_id1, valid_id2]
            )
        ],
        reviewer_status=DraftReviewerStatus.DRAFT,
        reviewer_id=None,
        reviewed_at=None,
        created_at=None,  # type: ignore
    )

    service = PolicyService()
    decisions = service.evaluate_draft(draft, context)

    assert len(decisions) == 1
    assert decisions[0].outcome == PolicyOutcome.PASS


def test_provenance_integrity_rule_fails() -> None:
    valid_id1 = uuid.uuid4()
    invalid_id = uuid.uuid4()

    context = SafeContext(
        system_instructions="",
        task_instructions="",
        output_schema={},
        policy_constraints=[],
        knowledge_passages=[
            ContextPassage(
                content="fact 1",
                origin=ContentOrigin.KNOWLEDGE,
                source_id=valid_id1,
                citation_locator=None,
            )
        ],
        patient_evidence=[],
        stt_transcripts=[],
        ocr_content=[],
        extracted_facts=[],
        timeline_events=[],
        missing_information=[],
        conflicting_information=[],
        retrieval_metadata=None,
    )

    draft = AIDraft(
        draft_id=uuid.uuid4(),
        ai_run_id=uuid.uuid4(),
        content={},
        validation_status=ValidationStatus.ACCEPTED,
        validation_errors=[],
        claim_provenance=[
            ClaimProvenance(
                claim_text="xyz", status="SUPPORTED", supporting_source_ids=[valid_id1, invalid_id]
            )
        ],
        reviewer_status=DraftReviewerStatus.DRAFT,
        reviewer_id=None,
        reviewed_at=None,
        created_at=None,  # type: ignore
    )

    service = PolicyService()
    decisions = service.evaluate_draft(draft, context)

    assert len(decisions) == 1
    assert decisions[0].outcome == PolicyOutcome.FAIL

    detail = decisions[0].detail
    assert isinstance(detail, dict)
    assert "invalid_source_ids" in detail
    assert str(invalid_id) in detail["invalid_source_ids"]
