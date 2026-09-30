"""
Unit tests for MissingInfoEvaluator and ChecklistLoader.
"""

import json
import uuid
from pathlib import Path

import pytest

from careintel.application.structuring.checklist_loader import (
    ChecklistLoader,
    ChecklistNotFoundError,
)
from careintel.application.structuring.missing_info_evaluator import MissingInfoEvaluator
from careintel.domain.structuring.checklist import ChecklistPolicy, ChecklistRequirement
from careintel.domain.structuring.conflicts import ConflictRecord, ConflictStatus
from careintel.domain.structuring.missing_info import RequirementStatus
from careintel.persistence.models.processing import ExtractedCandidateORM


def test_checklist_loader_success(tmp_path: Path) -> None:
    policy_data = {
        "version": "demo_v1",
        "max_questions_per_round": 3,
        "max_rounds": 2,
        "requirements": [
            {
                "key": "symptom_onset",
                "description": "When did the symptoms start?",
                "materiality": "HIGH",
                "expected_field_types": ["symptom_onset"],
            }
        ],
    }
    file_path = tmp_path / "demo_policy.json"
    file_path.write_text(json.dumps(policy_data))

    policy = ChecklistLoader.load(str(file_path), "demo_v1")
    assert policy.version == "demo_v1"
    assert policy.max_questions_per_round == 3
    assert len(policy.requirements) == 1
    assert policy.requirements[0].key == "symptom_onset"


def test_checklist_loader_version_mismatch(tmp_path: Path) -> None:
    policy_data = {"version": "demo_v1", "requirements": []}
    file_path = tmp_path / "demo_policy.json"
    file_path.write_text(json.dumps(policy_data))

    with pytest.raises(ChecklistNotFoundError, match="Version mismatch"):
        ChecklistLoader.load(str(file_path), "demo_v2")


def test_missing_info_evaluator_satisfied() -> None:
    policy = ChecklistPolicy(
        version="demo_v1",
        max_questions_per_round=5,
        max_rounds=2,
        requirements=[
            ChecklistRequirement(
                key="symptom_onset",
                description="Onset",
                materiality="HIGH",
                version="demo_v1",
                expected_field_types=["symptom_onset"],
            )
        ],
    )

    c1 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=uuid.uuid4(),
        field_type="symptom_onset",
        value="yesterday",
        status="VERIFIED",
    )

    items = MissingInfoEvaluator.evaluate(
        case_id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        candidates=[c1],
        conflicts=[],
        policy=policy,
    )

    assert len(items) == 1
    assert items[0].status == RequirementStatus.SATISFIED
    assert items[0].requirement_key == "symptom_onset"
    assert c1.id in items[0].evidence_candidates


def test_missing_info_evaluator_preserves_unverified_candidate() -> None:
    policy = ChecklistPolicy(
        version="demo_v1",
        max_questions_per_round=5,
        max_rounds=2,
        requirements=[
            ChecklistRequirement(
                key="symptom_onset",
                description="Onset",
                materiality="DEMO",
                version="demo_v1",
                expected_field_types=["symptom_onset"],
            )
        ],
    )
    candidate = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=uuid.uuid4(),
        field_type="symptom_onset",
        value="yesterday",
        status="CANDIDATE",
    )

    item = MissingInfoEvaluator.evaluate(uuid.uuid4(), uuid.uuid4(), [candidate], [], policy)[0]

    assert item.status == RequirementStatus.UNVERIFIED
    assert item.resolution is None


def test_missing_info_evaluator_missing() -> None:
    policy = ChecklistPolicy(
        version="demo_v1",
        max_questions_per_round=5,
        max_rounds=2,
        requirements=[
            ChecklistRequirement(
                key="symptom_onset",
                description="Onset",
                materiality="HIGH",
                version="demo_v1",
                expected_field_types=["symptom_onset"],
            )
        ],
    )

    c1 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=uuid.uuid4(),
        field_type="medication",
        value="Aspirin",
    )

    items = MissingInfoEvaluator.evaluate(
        case_id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        candidates=[c1],
        conflicts=[],
        policy=policy,
    )

    assert len(items) == 1
    assert items[0].status == RequirementStatus.MISSING
    assert len(items[0].evidence_candidates) == 0


def test_missing_info_evaluator_unreadable() -> None:
    policy = ChecklistPolicy(
        version="demo_v1",
        max_questions_per_round=5,
        max_rounds=2,
        requirements=[
            ChecklistRequirement(
                key="symptom_onset",
                description="Onset",
                materiality="HIGH",
                version="demo_v1",
                expected_field_types=["symptom_onset"],
            )
        ],
    )

    c1 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=uuid.uuid4(),
        field_type="symptom_onset",
        value="   ",
    )

    items = MissingInfoEvaluator.evaluate(
        case_id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        candidates=[c1],
        conflicts=[],
        policy=policy,
    )

    assert len(items) == 1
    assert items[0].status == RequirementStatus.UNREADABLE
    assert c1.id in items[0].evidence_candidates


def test_missing_info_evaluator_conflicting() -> None:
    policy = ChecklistPolicy(
        version="demo_v1",
        max_questions_per_round=5,
        max_rounds=2,
        requirements=[
            ChecklistRequirement(
                key="symptom_onset",
                description="Onset",
                materiality="HIGH",
                version="demo_v1",
                expected_field_types=["symptom_onset"],
            )
        ],
    )

    c1 = ExtractedCandidateORM(
        id=uuid.uuid4(),
        extraction_run_id=uuid.uuid4(),
        field_type="symptom_onset",
        value="Monday",
    )

    conflict = ConflictRecord(
        conflict_id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        field_type="symptom_onset",
        candidate_ids=[c1.id, uuid.uuid4()],
        status=ConflictStatus.OPEN,
        detection_run_id=uuid.uuid4(),
    )

    items = MissingInfoEvaluator.evaluate(
        case_id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        candidates=[c1],
        conflicts=[conflict],
        policy=policy,
    )

    assert len(items) == 1
    assert items[0].status == RequirementStatus.CONFLICTING
