"""
Demo Extraction Provider.
"""

import re
import uuid

from careintel.domain.processing.processing_models import CandidateField, ExtractionProvenance
from careintel.infrastructure.extraction.port import ExtractionProvider, ExtractionResult


class DemoExtractionProvider(ExtractionProvider):
    """
    Deterministic fake Extraction provider for testing.
    Does NOT use AI.
    """

    async def extract_candidates(
        self, text: str, run_id: str, evidence_id: uuid.UUID
    ) -> ExtractionResult:
        run_uuid = uuid.UUID(run_id)

        # A simple fake rule-based extraction for testing purposes
        candidates = []
        fever_start = text.lower().find("fever")
        if fever_start >= 0:
            candidates.append(
                CandidateField(
                    candidate_id=uuid.uuid4(),
                    run_id=run_uuid,
                    field_type="symptom",
                    value="fever",
                    normalized_value="Fever",
                    confidence=0.8,
                    provenance=[
                        ExtractionProvenance(
                            evidence_id=evidence_id,
                            span_start=fever_start,
                            span_end=fever_start + len("fever"),
                            raw_source_text=text[fever_start : fever_start + len("fever")],
                        )
                    ],
                )
            )

        date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        if date_match is not None:
            candidates.append(
                CandidateField(
                    candidate_id=uuid.uuid4(),
                    run_id=run_uuid,
                    field_type="symptom_onset",
                    value=date_match.group(0),
                    normalized_value=date_match.group(0),
                    confidence=None,
                    provenance=[
                        ExtractionProvenance(
                            evidence_id=evidence_id,
                            span_start=date_match.start(),
                            span_end=date_match.end(),
                            raw_source_text=date_match.group(0),
                        )
                    ],
                )
            )

        return ExtractionResult(
            candidates=candidates,
            provider_version="demo-extraction-v1",
        )
