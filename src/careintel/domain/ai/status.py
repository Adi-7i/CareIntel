"""
AI domain — task types, run status, and policy enums.
"""

from __future__ import annotations

from enum import StrEnum


class TaskType(StrEnum):
    """
    Bounded AI task types.

    The AI must operate inside these explicit task contracts.
    No generic "ask GPT" endpoint exists.

    REVIEWER_NOTE_DRAFT  — Draft a structured reviewer note based on case evidence.
    EVIDENCE_SUMMARY     — Summarize structured evidence for reviewer display.
    STRUCTURED_CASE_SUMMARY — Produce a structured case overview for handoff.
    CLARIFICATION_SUPPORT   — Generate clarification context for an open question.
    """

    REVIEWER_NOTE_DRAFT = "reviewer_note_draft"
    EVIDENCE_SUMMARY = "evidence_summary"
    STRUCTURED_CASE_SUMMARY = "structured_case_summary"
    CLARIFICATION_SUPPORT = "clarification_support"


class AIRunStatus(StrEnum):
    """
    Lifecycle status of an AI run.

    IN_PROGRESS     — AI call is ongoing.
    COMPLETED       — AI produced output that passed all validation.
    FAILED          — AI provider failed or timed out.
    REJECTED        — Output failed schema/domain/provenance validation.
    POLICY_BLOCKED  — Output failed deterministic safety policy check.
    """

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    POLICY_BLOCKED = "POLICY_BLOCKED"


class DraftReviewerStatus(StrEnum):
    """
    Reviewer decision status on an AI draft.

    DRAFT    — Awaiting reviewer action.
    APPROVED — Reviewer explicitly approved the draft.
    REJECTED — Reviewer rejected the draft.
    """

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ValidationStatus(StrEnum):
    """Status of the structured output validation pipeline."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REPAIR_ATTEMPTED = "REPAIR_ATTEMPTED"


class PolicyCheckType(StrEnum):
    """
    Types of deterministic policy checks applied to AI output.
    """

    ALLOWED_TASK = "ALLOWED_TASK"
    ALLOWED_OUTPUT_TYPE = "ALLOWED_OUTPUT_TYPE"
    REQUIRED_EVIDENCE = "REQUIRED_EVIDENCE"
    PROHIBITED_CONTENT = "PROHIBITED_CONTENT"
    REVIEWER_ONLY_ACTION = "REVIEWER_ONLY_ACTION"
    AUTHORIZATION = "AUTHORIZATION"
    CONSENT = "CONSENT"
    WORKFLOW_STATE = "WORKFLOW_STATE"
    PROVENANCE_REQUIREMENTS = "PROVENANCE_REQUIREMENTS"
    OUTPUT_SAFETY = "OUTPUT_SAFETY"


class PolicyOutcome(StrEnum):
    """Outcome of a single policy check."""

    PASS = "PASS"  # noqa: S105
    FAIL = "FAIL"
    WARN = "WARN"


class ContentOrigin(StrEnum):
    """
    Identifies the provenance of a SafeContext passage.

    Used to structurally label untrusted data so it is never
    confused with system instructions.
    """

    KNOWLEDGE = "KNOWLEDGE"
    PATIENT_TEXT = "PATIENT_TEXT"
    STT_TRANSCRIPT = "STT_TRANSCRIPT"
    OCR = "OCR"
    EXTRACTED_FACT = "EXTRACTED_FACT"
    TIMELINE_EVENT = "TIMELINE_EVENT"
    MISSING_INFO = "MISSING_INFO"
    CONFLICTING_INFO = "CONFLICTING_INFO"
    TRANSLATED = "TRANSLATED"
