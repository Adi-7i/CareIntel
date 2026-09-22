"""
Processing Commands.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from careintel.domain.processing.processor_type import ProcessorType


@dataclass(frozen=True)
class TriggerProcessingCommand:
    """Command to initiate a processing run."""

    evidence_id: uuid.UUID
    processor_type: ProcessorType
    parameters: dict[str, Any] = field(default_factory=dict)
