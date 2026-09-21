"""
Unit tests for ConflictDetector.
"""

import uuid

from careintel.application.structuring.conflict_detector import (
    ConflictDetector,
    DemoCompatibilityPolicy,
)
from careintel.domain.structuring.conflicts import ConflictStatus
from careintel.persistence.models.processing import ExtractedCandidateORM


def test_conflict_detector_no_conflict_on_same_value() -> None:
    c1 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=uuid.uuid4(),
        field_type="symptom_onset",
        value="Monday",
        normalized_value="Monday",
    )
    c2 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=c1.extraction_run_id,
        field_type="symptom_onset",
        value="monday",
        normalized_value="Monday",
    )

    case_id = uuid.uuid4()
    run_id = uuid.uuid4()
    policy = DemoCompatibilityPolicy()

    records = ConflictDetector.detect(case_id, run_id, [c1, c2], policy)
    assert len(records) == 0


def test_conflict_detector_detects_conflict() -> None:
    c1 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=uuid.uuid4(),
        field_type="symptom_onset",
        value="Monday",
        normalized_value="Monday",
    )
    c2 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=c1.extraction_run_id,
        field_type="symptom_onset",
        value="Tuesday",
        normalized_value="Tuesday",
    )

    case_id = uuid.uuid4()
    run_id = uuid.uuid4()
    policy = DemoCompatibilityPolicy()

    records = ConflictDetector.detect(case_id, run_id, [c1, c2], policy)
    assert len(records) == 1

    record = records[0]
    assert record.case_id == case_id
    assert record.detection_run_id == run_id
    assert record.field_type == "symptom_onset"
    assert record.status == ConflictStatus.OPEN
    # Both candidates must be preserved
    assert len(record.candidate_ids) == 2
    assert c1.id in record.candidate_ids
    assert c2.id in record.candidate_ids


def test_conflict_detector_ignores_other_fields() -> None:
    c1 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=uuid.uuid4(),
        field_type="medication",
        value="Aspirin",
    )
    c2 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=c1.extraction_run_id,
        field_type="medication",
        value="Tylenol",
    )

    case_id = uuid.uuid4()
    run_id = uuid.uuid4()
    policy = DemoCompatibilityPolicy()

    # The demo policy considers different medications as non-conflicting.
    records = ConflictDetector.detect(case_id, run_id, [c1, c2], policy)
    assert len(records) == 0
