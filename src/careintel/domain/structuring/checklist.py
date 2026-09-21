"""
Checklist and Policy domain models.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChecklistRequirement:
    """
    A single requirement in a checklist policy.
    """

    key: str
    description: str
    materiality: str
    version: str
    expected_field_types: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChecklistPolicy:
    """
    A versioned checklist policy defining required information bounds.
    """

    version: str
    max_questions_per_round: int
    max_rounds: int
    requirements: list[ChecklistRequirement] = field(default_factory=list)
