"""
Missing information evaluation logic.
"""

from __future__ import annotations

import datetime
import uuid

from careintel.domain.structuring.checklist import ChecklistPolicy
from careintel.domain.structuring.conflicts import ConflictRecord
from careintel.domain.structuring.missing_info import MissingInfoItem, RequirementStatus
from careintel.persistence.models.processing import ExtractedCandidateORM


class MissingInfoEvaluator:
    """
    Evaluates a case against a loaded ChecklistPolicy.
    """

    @staticmethod
    def evaluate(
        case_id: uuid.UUID,
        run_id: uuid.UUID,
        candidates: list[ExtractedCandidateORM],
        conflicts: list[ConflictRecord],
        policy: ChecklistPolicy,
    ) -> list[MissingInfoItem]:
        """
        Evaluate checklist requirements and return MissingInfoItems.
        """
        items: list[MissingInfoItem] = []
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

        # Map field types to candidates
        candidates_by_field: dict[str, list[ExtractedCandidateORM]] = {}
        for c in candidates:
            candidates_by_field.setdefault(c.field_type, []).append(c)

        # Map field types to conflict records
        conflicts_by_field: dict[str, list[ConflictRecord]] = {}
        for cr in conflicts:
            conflicts_by_field.setdefault(cr.field_type, []).append(cr)

        for req in policy.requirements:
            req_candidates: list[ExtractedCandidateORM] = []
            for ft in req.expected_field_types:
                req_candidates.extend(candidates_by_field.get(ft, []))

            req_conflicts: list[ConflictRecord] = []
            for ft in req.expected_field_types:
                req_conflicts.extend(conflicts_by_field.get(ft, []))

            candidate_ids = [c.id for c in req_candidates]

            # Determine Status
            status = RequirementStatus.MISSING
            resolution = None

            if not req_candidates:
                status = RequirementStatus.MISSING
            elif req_conflicts:
                status = RequirementStatus.CONFLICTING
            else:
                # Check if all candidates are unreadable/empty
                has_readable = False
                for c in req_candidates:
                    val = (c.normalized_value or c.value).strip()
                    if val:
                        has_readable = True
                        break

                if not has_readable:
                    status = RequirementStatus.UNREADABLE
                else:
                    # In a real system, we'd check against UNVERIFIED thresholds here
                    # For prototype, if it's readable and not conflicting, it's SATISFIED
                    status = RequirementStatus.SATISFIED
                    resolution = "Found matching extracted information."

            item = MissingInfoItem(
                item_id=uuid.uuid4(),
                case_id=case_id,
                evaluation_run_id=run_id,
                requirement_key=req.key,
                checklist_version=policy.version,
                status=status,
                materiality=req.materiality,
                evidence_candidates=candidate_ids,
                resolution=resolution,
                created_at=now,
            )
            items.append(item)

        return items
