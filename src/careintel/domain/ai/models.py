"""
AI domain models.

Value objects for the AI execution, context, validation, and policy layers.

CRITICAL INVARIANTS:
- AI output is a DRAFT until explicitly approved by a human reviewer.
- AI cannot approve its own output, finalize disposition, or bypass consent.
- All factual AI claims must be traceable to retrieval sources where applicable.
- The PolicyService is independent from the LLM and is the final safety authority.
- No diagnostic conclusions, prescriptions, or clinical decisions may be generated.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field

from careintel.domain.ai.status import (
    AIRunStatus,
    ContentOrigin,
    DraftReviewerStatus,
    PolicyCheckType,
    PolicyOutcome,
    TaskType,
    ValidationStatus,
)

# ── Safe Context ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ContextPassage:
    """
    A single passage included in the AI context.

    All passages are clearly labeled with their origin so the AI
    receives structural signals distinguishing trusted knowledge
    from untrusted patient data.

    The `content` field is ALWAYS treated as untrusted data regardless
    of origin, except for KNOWLEDGE passages which are from the
    institutional corpus.

    IMPORTANT: Even KNOWLEDGE passages cannot override system instructions.
    """

    content: str
    origin: ContentOrigin
    # Provenance pointer: knowledge_chunks.id, evidence.id, segment.id, etc.
    source_id: uuid.UUID | None
    # Human-readable citation for reviewer-facing display
    citation_locator: str | None


@dataclass(frozen=True)
class RetrievalMetadataRef:
    """Reference to a completed retrieval run for audit purposes."""

    retrieval_run_id: uuid.UUID
    query_hash: str
    candidate_count: int
    corpus_version: str | None


@dataclass(frozen=True)
class SafeContext:
    """
    Structurally separates system instructions from untrusted external data.

    TRUSTED sections (written exclusively by application code):
    - system_instructions: Never derived from external input.
    - task_instructions: Task-specific prompt, versioned.
    - output_schema: JSON schema defining valid output structure.
    - policy_constraints: Explicit constraints the AI must observe.

    UNTRUSTED DATA sections (labeled, clearly delineated):
    - All other sections contain external content treated as data only.
    - External content CANNOT change system behavior regardless of its text.

    The structural separation makes prompt injection ineffective:
    injected content in patient/OCR/transcript text appears only in
    data sections and cannot access system instruction context.
    """

    # ── TRUSTED — application-controlled ────────────────────────────────────
    system_instructions: str
    task_instructions: str
    output_schema: dict[str, object]  # JSON schema as dict
    policy_constraints: list[str]

    # ── UNTRUSTED DATA — external content ───────────────────────────────────
    knowledge_passages: list[ContextPassage]
    patient_evidence: list[ContextPassage]
    stt_transcripts: list[ContextPassage]
    ocr_content: list[ContextPassage]
    extracted_facts: list[ContextPassage]
    timeline_events: list[ContextPassage]
    missing_information: list[ContextPassage]
    conflicting_information: list[ContextPassage]

    # ── Retrieval audit metadata ─────────────────────────────────────────────
    retrieval_metadata: RetrievalMetadataRef | None


# ── AI Run Record ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AITaskConfig:
    """
    Configuration for a single AI task execution.

    Versioned so historical runs remain explainable.
    """

    task_type: TaskType
    provider: str
    model: str
    prompt_version: str
    schema_version: str
    timeout_seconds: int


@dataclass(frozen=True)
class AIRunRecord:
    """
    Domain record for a single AI execution attempt.
    """

    run_id: uuid.UUID
    case_id: uuid.UUID
    actor_id: uuid.UUID
    task_type: TaskType
    provider: str
    model: str
    prompt_version: str
    schema_version: str
    retrieval_run_id: uuid.UUID | None
    status: AIRunStatus
    input_hash: str | None  # SHA-256 of serialized context
    output_hash: str | None  # SHA-256 of raw AI response
    latency_ms: int | None
    usage: dict[str, int]  # e.g. {'prompt_tokens': 500, 'completion_tokens': 200}
    error_category: str | None
    failure_reason: str | None
    created_at: datetime.datetime


# ── Validation ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ValidationError:
    """A single validation failure in the output pipeline."""

    step: str  # e.g. 'schema', 'domain', 'source', 'provenance', 'prohibited'
    code: str  # Machine-readable error code
    detail: str  # Human-readable description


@dataclass(frozen=True)
class ClaimProvenance:
    """
    Provenance tracing for a factual claim in an AI draft.

    SUPPORTED          — Claim is backed by a retrieval candidate.
    UNSUPPORTED        — No retrieval candidate supports this claim.
    PARTIALLY_SUPPORTED — Some but not all aspects are supported.
    MISSING_EVIDENCE    — The claim acknowledges missing evidence.
    CONFLICTING_EVIDENCE — Conflicting sources exist for this claim.
    """

    claim_text: str
    status: str  # 'SUPPORTED', 'UNSUPPORTED', 'PARTIALLY_SUPPORTED', etc.
    supporting_source_ids: list[uuid.UUID] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of the full structured output validation pipeline.
    """

    status: ValidationStatus
    errors: list[ValidationError] = field(default_factory=list)
    claim_provenance: list[ClaimProvenance] = field(default_factory=list)


# ── AI Draft ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AIDraft:
    """
    A validated AI-generated draft awaiting reviewer decision.

    A draft is NEVER clinically authoritative.
    Reviewer approval is required before any draft affects case state.
    """

    draft_id: uuid.UUID
    ai_run_id: uuid.UUID
    # Validated structured content (task-specific schema)
    content: dict[str, object]
    validation_status: ValidationStatus
    validation_errors: list[ValidationError]
    # Provenance mapping: each factual claim → source identifiers
    claim_provenance: list[ClaimProvenance]
    reviewer_status: DraftReviewerStatus
    reviewer_id: uuid.UUID | None
    reviewed_at: datetime.datetime | None
    created_at: datetime.datetime


# ── Policy ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PolicyDecision:
    """
    Result of a single deterministic policy check.

    PolicyService runs independently from the LLM.
    Any FAIL outcome blocks the draft from being accepted.
    """

    check_type: PolicyCheckType
    policy_version: str
    outcome: PolicyOutcome
    detail: dict[str, object] = field(default_factory=dict)
