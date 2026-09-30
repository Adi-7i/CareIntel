"""
Unit tests for ClarificationQuestionGenerator.
"""

import datetime
import uuid

from careintel.application.structuring.question_generator import TemplateQuestionGenerator
from careintel.domain.structuring.checklist import ChecklistPolicy, ChecklistRequirement
from careintel.domain.structuring.missing_info import MissingInfoItem, RequirementStatus
from careintel.domain.structuring.questions import ClarificationQuestion, QuestionStatus


def test_question_generator_skips_satisfied() -> None:
    generator = TemplateQuestionGenerator()
    policy = ChecklistPolicy(version="demo_v1", max_questions_per_round=5, max_rounds=2)
    item = MissingInfoItem(
        item_id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        evaluation_run_id=uuid.uuid4(),
        requirement_key="symptom_onset",
        checklist_version="demo_v1",
        status=RequirementStatus.SATISFIED,
        materiality="HIGH",
        created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
    )

    q = generator.generate(item, policy, [], 1)
    assert q is None


def test_question_generator_skips_max_rounds() -> None:
    generator = TemplateQuestionGenerator()
    policy = ChecklistPolicy(version="demo_v1", max_questions_per_round=5, max_rounds=2)
    item = MissingInfoItem(
        item_id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        evaluation_run_id=uuid.uuid4(),
        requirement_key="symptom_onset",
        checklist_version="demo_v1",
        status=RequirementStatus.MISSING,
        materiality="HIGH",
        created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
    )

    q = generator.generate(item, policy, [], 3)
    assert q is None


def test_question_generator_skips_existing_question() -> None:
    generator = TemplateQuestionGenerator()
    policy = ChecklistPolicy(version="demo_v1", max_questions_per_round=5, max_rounds=2)
    item = MissingInfoItem(
        item_id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        evaluation_run_id=uuid.uuid4(),
        requirement_key="symptom_onset",
        checklist_version="demo_v1",
        status=RequirementStatus.MISSING,
        materiality="HIGH",
        created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
    )

    existing_q = ClarificationQuestion(
        question_id=uuid.uuid4(),
        case_id=item.case_id,
        evaluation_run_id=uuid.uuid4(),
        requirement_key="symptom_onset",
        missing_item_id=uuid.uuid4(),
        question_text="When?",
        round_number=1,
        status=QuestionStatus.ANSWERED,
        generator_version="template_v1",
        created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
    )

    q = generator.generate(item, policy, [existing_q], 2)
    assert q is None


def test_question_generator_generates_valid_question() -> None:
    generator = TemplateQuestionGenerator()
    policy = ChecklistPolicy(
        version="demo_v1",
        max_questions_per_round=5,
        max_rounds=2,
        requirements=[
            ChecklistRequirement(
                key="symptom_onset",
                description="when the reported symptom started",
                materiality="DEMO",
                version="demo_v1",
                expected_field_types=["symptom_onset"],
            )
        ],
    )
    item = MissingInfoItem(
        item_id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        evaluation_run_id=uuid.uuid4(),
        requirement_key="symptom_onset",
        checklist_version="demo_v1",
        status=RequirementStatus.MISSING,
        materiality="HIGH",
        created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
    )

    q = generator.generate(item, policy, [], 1)
    assert q is not None
    assert q.requirement_key == "symptom_onset"
    assert q.missing_item_id == item.item_id
    assert q.case_id == item.case_id
    assert q.status == QuestionStatus.PENDING
    assert q.round_number == 1
    assert "symptom" in q.question_text.lower()
