"""Strict structured-output and provenance validation for advisory AI drafts."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError

from careintel.domain.ai.models import (
    ClaimProvenance,
    SafeContext,
    ValidationError,
    ValidationResult,
)
from careintel.domain.ai.status import ValidationStatus


class AdvisoryClaim(BaseModel):
    """One explicitly sourced assertion in an advisory draft."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=4000)
    status: Literal[
        "SUPPORTED",
        "UNSUPPORTED",
        "PARTIALLY_SUPPORTED",
        "MISSING_EVIDENCE",
        "CONFLICTING_EVIDENCE",
    ]
    supporting_source_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)


class AdvisoryOutput(BaseModel):
    """Bounded output shape shared by the current advisory task types."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=12000)
    claims: list[AdvisoryClaim] = Field(default_factory=list, max_length=100)
    missing_information_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    limitations: list[str] = Field(default_factory=list, max_length=50)


def advisory_output_schema() -> dict[str, object]:
    """Return the strict provider schema from the same model used for validation."""
    return AdvisoryOutput.model_json_schema()


def validate_advisory_output(
    raw: dict[str, object], context: SafeContext
) -> tuple[AdvisoryOutput | None, ValidationResult]:
    """Run schema, identifier, source, provenance, and missing-info checks."""
    errors: list[ValidationError] = []
    try:
        output = AdvisoryOutput.model_validate(raw)
    except PydanticValidationError as exc:
        for item in exc.errors(include_url=False):
            location = ".".join(str(part) for part in item["loc"])
            errors.append(
                ValidationError(
                    step="schema",
                    code=str(item["type"]),
                    detail=f"{location}: {item['msg']}",
                )
            )
        return None, ValidationResult(status=ValidationStatus.REJECTED, errors=errors)

    all_passages = (
        context.knowledge_passages
        + context.patient_evidence
        + context.stt_transcripts
        + context.ocr_content
        + context.extracted_facts
        + context.timeline_events
        + context.missing_information
        + context.conflicting_information
    )
    valid_source_ids = {item.source_id for item in all_passages if item.source_id is not None}
    valid_missing_ids = {
        item.source_id for item in context.missing_information if item.source_id is not None
    }
    provenance: list[ClaimProvenance] = []

    for index, claim in enumerate(output.claims):
        source_ids = set(claim.supporting_source_ids)
        invalid = source_ids - valid_source_ids
        if invalid:
            errors.append(
                ValidationError(
                    step="source",
                    code="UNKNOWN_SOURCE_ID",
                    detail=f"claims.{index} cites a source outside the case context.",
                )
            )
        if claim.status == "SUPPORTED" and not source_ids:
            errors.append(
                ValidationError(
                    step="provenance",
                    code="SUPPORTED_WITHOUT_SOURCE",
                    detail=f"claims.{index} is marked supported without a source.",
                )
            )
        if claim.status in {"UNSUPPORTED", "MISSING_EVIDENCE"} and source_ids:
            errors.append(
                ValidationError(
                    step="provenance",
                    code="UNSUPPORTED_WITH_SOURCE",
                    detail=f"claims.{index} has an incompatible provenance state.",
                )
            )
        provenance.append(
            ClaimProvenance(
                claim_text=claim.text,
                status=claim.status,
                supporting_source_ids=claim.supporting_source_ids,
            )
        )

    unknown_missing = set(output.missing_information_ids) - valid_missing_ids
    if unknown_missing:
        errors.append(
            ValidationError(
                step="missing_information",
                code="UNKNOWN_MISSING_INFORMATION_ID",
                detail=(
                    "Output references missing-information identifiers outside the case context."
                ),
            )
        )

    return output, ValidationResult(
        status=ValidationStatus.REJECTED if errors else ValidationStatus.ACCEPTED,
        errors=errors,
        claim_provenance=provenance,
    )
