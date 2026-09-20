"""
Demo Extraction Provider.
"""

import uuid

from careintel.domain.processing.processing_models import CandidateField
from careintel.infrastructure.extraction.port import ExtractionProvider, ExtractionResult


class DemoExtractionProvider(ExtractionProvider):
    """
    Deterministic fake Extraction provider for testing.
    Does NOT use AI.
    """

    async def extract_candidates(self, text: str, run_id: str) -> ExtractionResult:
        run_uuid = uuid.UUID(run_id)

        # A simple fake rule-based extraction for testing purposes
        candidates = []
        if "fever" in text.lower():
            candidates.append(
                CandidateField(
                    candidate_id=uuid.uuid4(),
                    run_id=run_uuid,
                    field_type="symptom",
                    value="fever",
                    normalized_value="Fever",
                    confidence=0.8,
                )
            )

        return ExtractionResult(
            candidates=candidates,
            provider_version="demo-extraction-v1",
        )
