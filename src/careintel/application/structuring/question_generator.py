"""
Clarification question generation logic.
"""

from __future__ import annotations

import datetime
import uuid
from typing import ClassVar, Protocol

from careintel.domain.structuring.checklist import ChecklistPolicy
from careintel.domain.structuring.missing_info import MissingInfoItem, RequirementStatus
from careintel.domain.structuring.questions import ClarificationQuestion, QuestionStatus


class ClarificationQuestionGenerator(Protocol):
    def generate(
        self,
        item: MissingInfoItem,
        policy: ChecklistPolicy,
        existing_questions: list[ClarificationQuestion],
        round_number: int,
    ) -> ClarificationQuestion | None: ...


class TemplateQuestionGenerator:
    """
    Deterministic template-based generator.
    """

    VERSION = "template_v1"

    # In a real system, these templates would be stored in the checklist policy itself.
    # For this prototype, we define a few basic templates.
    _TEMPLATES: ClassVar[dict[str, str]] = {
        "symptom_onset": "When did you first notice the symptoms?",
        "medication_name": "What is the name of the medication you are taking?",
        "severity": "How severe are your symptoms on a scale of 1 to 10?",
    }

    def generate(
        self,
        item: MissingInfoItem,
        policy: ChecklistPolicy,
        existing_questions: list[ClarificationQuestion],
        round_number: int,
    ) -> ClarificationQuestion | None:
        """
        Generate a clarification question if the requirement is unmet and allowed by policy.
        """
        if item.status == RequirementStatus.SATISFIED:
            return None

        if round_number > policy.max_rounds:
            return None

        # Check if we already asked this question in ANY round
        for eq in existing_questions:
            if eq.requirement_key == item.requirement_key:
                return None

        template = self._TEMPLATES.get(
            item.requirement_key,
            f"Could you provide more information regarding: {item.requirement_key}?",
        )

        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

        return ClarificationQuestion(
            question_id=uuid.uuid4(),
            case_id=item.case_id,
            evaluation_run_id=item.evaluation_run_id,
            requirement_key=item.requirement_key,
            missing_item_id=item.item_id,
            question_text=template,
            round_number=round_number,
            status=QuestionStatus.PENDING,
            generator_version=self.VERSION,
            created_at=now,
        )
