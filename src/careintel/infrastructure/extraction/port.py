"""
Extraction Provider interface.
"""

import uuid
from typing import Protocol

from careintel.domain.processing.processing_models import CandidateField


class ExtractionResult:
    """Standardized Extraction output."""

    def __init__(self, candidates: list[CandidateField], provider_version: str) -> None:
        self.candidates = candidates
        self.provider_version = provider_version


class ExtractionProvider(Protocol):
    """Protocol for Extraction adapters (e.g., GPT, Demo)."""

    async def extract_candidates(
        self, text: str, run_id: str, evidence_id: uuid.UUID
    ) -> ExtractionResult:
        """
        Extract structured candidates from normalized text.
        """
        ...
