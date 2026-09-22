"""
Checklist loader logic.
"""

from __future__ import annotations

import json
from pathlib import Path

from careintel.domain.structuring.checklist import ChecklistPolicy, ChecklistRequirement


class ChecklistNotFoundError(Exception):
    """Raised when the specified checklist policy cannot be found or parsed."""

    pass


class ChecklistLoader:
    """
    Loads versioned ChecklistPolicy from the filesystem.
    """

    @staticmethod
    def load(file_path: str, expected_version: str) -> ChecklistPolicy:
        """
        Load a checklist policy from a JSON file.
        Raises ChecklistNotFoundError if missing, malformed, or version mismatch.
        """
        path = Path(file_path)
        if not path.is_file():
            raise ChecklistNotFoundError(f"Checklist file not found: {file_path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ChecklistNotFoundError(f"Failed to parse checklist JSON: {e}") from e

        if data.get("version") != expected_version:
            raise ChecklistNotFoundError(
                f"Version mismatch. Expected {expected_version}, got {data.get('version')}"
            )

        requirements = []
        for req_data in data.get("requirements", []):
            requirements.append(
                ChecklistRequirement(
                    key=req_data["key"],
                    description=req_data["description"],
                    materiality=req_data["materiality"],
                    version=data["version"],
                    expected_field_types=req_data.get("expected_field_types", []),
                )
            )

        return ChecklistPolicy(
            version=data["version"],
            max_questions_per_round=data.get("max_questions_per_round", 5),
            max_rounds=data.get("max_rounds", 2),
            requirements=requirements,
        )
