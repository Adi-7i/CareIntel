"""Structured AI output validation tests."""

import uuid

from careintel.application.ai.output_validation import validate_advisory_output
from careintel.domain.ai.models import ContextPassage, SafeContext
from careintel.domain.ai.status import ContentOrigin, ValidationStatus


def _context() -> tuple[SafeContext, uuid.UUID, uuid.UUID]:
    source_id = uuid.uuid4()
    missing_id = uuid.uuid4()
    return (
        SafeContext(
            system_instructions="trusted",
            task_instructions="bounded",
            output_schema={},
            policy_constraints=[],
            knowledge_passages=[
                ContextPassage("source", ContentOrigin.KNOWLEDGE, source_id, "synthetic")
            ],
            patient_evidence=[],
            stt_transcripts=[],
            ocr_content=[],
            extracted_facts=[],
            timeline_events=[],
            missing_information=[
                ContextPassage("missing", ContentOrigin.MISSING_INFO, missing_id, "synthetic")
            ],
            conflicting_information=[],
            retrieval_metadata=None,
        ),
        source_id,
        missing_id,
    )


def test_complete_validation_chain_accepts_known_sources_and_missing_ids() -> None:
    context, source_id, missing_id = _context()
    output, result = validate_advisory_output(
        {
            "summary": "Evidence-bound summary.",
            "claims": [
                {
                    "text": "Synthetic source contains a statement.",
                    "status": "SUPPORTED",
                    "supporting_source_ids": [str(source_id)],
                }
            ],
            "missing_information_ids": [str(missing_id)],
            "limitations": ["Human review required."],
        },
        context,
    )

    assert output is not None
    assert result.status == ValidationStatus.ACCEPTED
    assert result.errors == []
    assert result.claim_provenance[0].supporting_source_ids == [source_id]


def test_validation_rejects_unknown_source_and_missing_identifier() -> None:
    context, _, _ = _context()
    output, result = validate_advisory_output(
        {
            "summary": "Unverified summary.",
            "claims": [
                {
                    "text": "Unsupported cross-case assertion.",
                    "status": "SUPPORTED",
                    "supporting_source_ids": [str(uuid.uuid4())],
                }
            ],
            "missing_information_ids": [str(uuid.uuid4())],
            "limitations": [],
        },
        context,
    )

    assert output is not None
    assert result.status == ValidationStatus.REJECTED
    assert {error.code for error in result.errors} == {
        "UNKNOWN_SOURCE_ID",
        "UNKNOWN_MISSING_INFORMATION_ID",
    }


def test_validation_rejects_workflow_field_at_schema_boundary() -> None:
    context, _, _ = _context()
    output, result = validate_advisory_output(
        {
            "summary": "Attempted action.",
            "claims": [],
            "missing_information_ids": [],
            "limitations": [],
            "workflow_action": "close case",
        },
        context,
    )

    assert output is None
    assert result.status == ValidationStatus.REJECTED
    assert any(error.step == "schema" for error in result.errors)
