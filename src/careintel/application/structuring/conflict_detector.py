"""
Conflict detection logic.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from careintel.domain.structuring.conflicts import ConflictRecord, ConflictStatus
from careintel.persistence.models.processing import ExtractedCandidateORM


class CompatibilityPolicy(Protocol):
    """
    Protocol for defining when two candidates are in material conflict.
    """

    def are_conflicting(self, c1: ExtractedCandidateORM, c2: ExtractedCandidateORM) -> bool:
        """
        Return True if c1 and c2 are in explicit material conflict.
        Return False if they are compatible, corroborate each other,
        or if it's uncertain.
        """
        ...


class DemoCompatibilityPolicy:
    """
    Extremely conservative demo policy.
    Real clinical conflict detection requires a much more robust engine.
    """

    def are_conflicting(self, c1: ExtractedCandidateORM, c2: ExtractedCandidateORM) -> bool:
        if c1.field_type != c2.field_type:
            return False

        # In a real system, multiple different medications are NOT a conflict.
        # But if the field_type is something inherently singular (like "birth_date"),
        # then different values might conflict.
        # For this prototype, we only define a conflict for "symptom_onset"
        # if the normalized values are strictly different.
        if c1.field_type == "symptom_onset":
            val1 = (c1.normalized_value or c1.value).strip().lower()
            val2 = (c2.normalized_value or c2.value).strip().lower()
            if val1 != val2:
                # If they are different string representations, we flag a potential conflict
                return True

        return False


class ConflictDetector:
    """
    Detects conflicts among extracted candidates using a given policy.
    """

    @staticmethod
    def detect(
        case_id: uuid.UUID,
        run_id: uuid.UUID,
        candidates: list[ExtractedCandidateORM],
        policy: CompatibilityPolicy,
    ) -> list[ConflictRecord]:
        """
        Evaluate candidates and return any detected ConflictRecords.
        ALL conflicting candidate IDs are preserved in the record.
        """
        records: list[ConflictRecord] = []

        # Group by field_type
        grouped: dict[str, list[ExtractedCandidateORM]] = {}
        for c in candidates:
            grouped.setdefault(c.field_type, []).append(c)

        for field_type, group in grouped.items():
            if len(group) < 2:
                continue

            # Naive O(N^2) comparison for prototype
            # In a real system we'd form conflict cliques.
            conflicting_ids: set[uuid.UUID] = set()
            for i, c1 in enumerate(group):
                for c2 in group[i + 1 :]:
                    if policy.are_conflicting(c1, c2):
                        conflicting_ids.add(c1.id)
                        conflicting_ids.add(c2.id)

            if conflicting_ids:
                records.append(
                    ConflictRecord(
                        conflict_id=uuid.uuid4(),
                        case_id=case_id,
                        field_type=field_type,
                        candidate_ids=list(conflicting_ids),
                        status=ConflictStatus.OPEN,
                        detection_run_id=run_id,
                    )
                )

        return records
