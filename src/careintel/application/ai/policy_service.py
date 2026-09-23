"""
Deterministic AI Safety Policy Service.

Evaluates validated AI drafts against deterministic safety and business rules.
Operates entirely independently from the LLM.

CRITICAL INVARIANTS:
- A draft MUST pass all policies to be presented to a human reviewer.
- A FAIL outcome immediately blocks the draft (status = POLICY_BLOCKED).
- Policy rules are deterministic, code-based checks, not LLM prompts.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, ClassVar, Protocol

from careintel.domain.ai.models import AIDraft, PolicyDecision, SafeContext
from careintel.domain.ai.status import PolicyCheckType, PolicyOutcome


class PolicyRule(Protocol):
    """Protocol for an individual deterministic policy rule."""

    @property
    def check_type(self) -> PolicyCheckType:
        """The type of policy this rule enforces."""
        ...

    @property
    def version(self) -> str:
        """Rule version for auditability."""
        ...

    def evaluate(self, draft: AIDraft, context: SafeContext) -> PolicyDecision:
        """
        Evaluate the draft against this rule.

        Returns:
            PolicyDecision with outcome PASS, WARN, or FAIL.
        """
        ...


class ProvenanceIntegrityRule:
    """
    Ensures that any source_id cited in the draft's claim provenance
    actually exists in the provided SafeContext.
    """

    @property
    def check_type(self) -> PolicyCheckType:
        return PolicyCheckType.PROVENANCE_REQUIREMENTS

    @property
    def version(self) -> str:
        return "1.0"

    def evaluate(self, draft: AIDraft, context: SafeContext) -> PolicyDecision:
        # Collect all valid source IDs from the context
        valid_ids: set[uuid.UUID] = set()

        def _collect(passages: list[Any]) -> None:
            for p in passages:
                if p.source_id is not None:
                    valid_ids.add(p.source_id)

        _collect(context.knowledge_passages)
        _collect(context.patient_evidence)
        _collect(context.stt_transcripts)
        _collect(context.ocr_content)
        _collect(context.extracted_facts)
        _collect(context.timeline_events)

        invalid_citations = []
        unsupported_claim_indexes = []
        for index, claim in enumerate(draft.claim_provenance):
            if claim.status == "SUPPORTED" and not claim.supporting_source_ids:
                unsupported_claim_indexes.append(index)
            for sid in claim.supporting_source_ids:
                if sid not in valid_ids:
                    invalid_citations.append(str(sid))

        if invalid_citations or unsupported_claim_indexes:
            return PolicyDecision(
                check_type=self.check_type,
                policy_version=self.version,
                outcome=PolicyOutcome.FAIL,
                detail={
                    "invalid_source_ids": invalid_citations,
                    "supported_without_source_indexes": unsupported_claim_indexes,
                },
            )

        return PolicyDecision(
            check_type=self.check_type,
            policy_version=self.version,
            outcome=PolicyOutcome.PASS,
            detail={},
        )


def _keys_and_strings(value: object) -> tuple[set[str], list[str]]:
    keys: set[str] = set()
    strings: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key).casefold())
            nested_keys, nested_strings = _keys_and_strings(nested)
            keys.update(nested_keys)
            strings.extend(nested_strings)
    elif isinstance(value, list):
        for nested in value:
            nested_keys, nested_strings = _keys_and_strings(nested)
            keys.update(nested_keys)
            strings.extend(nested_strings)
    elif isinstance(value, str):
        strings.append(value)
    return keys, strings


class AllowedOutputTypeRule:
    @property
    def check_type(self) -> PolicyCheckType:
        return PolicyCheckType.ALLOWED_OUTPUT_TYPE

    @property
    def version(self) -> str:
        return "1.0"

    def evaluate(self, draft: AIDraft, context: SafeContext) -> PolicyDecision:
        allowed = {"summary", "claims", "missing_information_ids", "limitations"}
        unexpected = sorted(set(draft.content) - allowed)
        return PolicyDecision(
            check_type=self.check_type,
            policy_version=self.version,
            outcome=PolicyOutcome.FAIL if unexpected else PolicyOutcome.PASS,
            detail={"unexpected_fields": unexpected} if unexpected else {},
        )


class RequiredEvidenceRule:
    @property
    def check_type(self) -> PolicyCheckType:
        return PolicyCheckType.REQUIRED_EVIDENCE

    @property
    def version(self) -> str:
        return "1.0"

    def evaluate(self, draft: AIDraft, context: SafeContext) -> PolicyDecision:
        missing = [
            index
            for index, claim in enumerate(draft.claim_provenance)
            if claim.status == "SUPPORTED" and not claim.supporting_source_ids
        ]
        return PolicyDecision(
            check_type=self.check_type,
            policy_version=self.version,
            outcome=PolicyOutcome.FAIL if missing else PolicyOutcome.PASS,
            detail={"claim_indexes": missing} if missing else {},
        )


class ProhibitedContentRule:
    _PROHIBITED_KEYS: ClassVar[set[str]] = {
        "diagnosis",
        "diagnoses",
        "prescription",
        "treatment_plan",
        "medication_recommendation",
        "dosage",
    }
    _PATTERN = re.compile(
        r"\b(?:diagnosis\s+is|diagnos(?:e|ed)\s+with|prescrib(?:e|ed|ing)|"
        r"dosage\s+should|treatment\s+plan\s+is)\b",
        re.IGNORECASE,
    )

    @property
    def check_type(self) -> PolicyCheckType:
        return PolicyCheckType.PROHIBITED_CONTENT

    @property
    def version(self) -> str:
        return "1.0"

    def evaluate(self, draft: AIDraft, context: SafeContext) -> PolicyDecision:
        keys, strings = _keys_and_strings(draft.content)
        prohibited_keys = sorted(keys & self._PROHIBITED_KEYS)
        matched_text = any(self._PATTERN.search(value) for value in strings)
        failed = bool(prohibited_keys or matched_text)
        return PolicyDecision(
            check_type=self.check_type,
            policy_version=self.version,
            outcome=PolicyOutcome.FAIL if failed else PolicyOutcome.PASS,
            detail={
                "prohibited_fields": prohibited_keys,
                "prohibited_text_detected": matched_text,
            }
            if failed
            else {},
        )


class ReviewerOnlyActionRule:
    _PROHIBITED_KEYS: ClassVar[set[str]] = {
        "approval",
        "approved",
        "urgency",
        "urgency_decision",
        "escalation",
        "referral",
        "case_closure",
        "workflow_action",
        "tool_call",
    }
    _PATTERN = re.compile(
        r"\b(?:approve|approved|escalate|escalated|refer|referred|close|closed)\s+"
        r"(?:the\s+|this\s+)?case\b|\bcase\s+urgency\s+is\b",
        re.IGNORECASE,
    )

    @property
    def check_type(self) -> PolicyCheckType:
        return PolicyCheckType.REVIEWER_ONLY_ACTION

    @property
    def version(self) -> str:
        return "1.0"

    def evaluate(self, draft: AIDraft, context: SafeContext) -> PolicyDecision:
        keys, strings = _keys_and_strings(draft.content)
        prohibited_keys = sorted(keys & self._PROHIBITED_KEYS)
        matched_text = any(self._PATTERN.search(value) for value in strings)
        failed = bool(prohibited_keys or matched_text)
        return PolicyDecision(
            check_type=self.check_type,
            policy_version=self.version,
            outcome=PolicyOutcome.FAIL if failed else PolicyOutcome.PASS,
            detail={
                "reviewer_only_fields": prohibited_keys,
                "reviewer_only_action_detected": matched_text,
            }
            if failed
            else {},
        )


class PolicyService:
    """
    Executes safety policies against an AI draft.
    """

    def __init__(self, rules: list[PolicyRule] | None = None) -> None:
        if rules is None:
            # Default safety suite
            self._rules: list[PolicyRule] = [
                AllowedOutputTypeRule(),
                RequiredEvidenceRule(),
                ProvenanceIntegrityRule(),
                ProhibitedContentRule(),
                ReviewerOnlyActionRule(),
            ]
        else:
            self._rules = rules

    def evaluate_draft(self, draft: AIDraft, context: SafeContext) -> list[PolicyDecision]:
        """
        Run all registered rules against the draft.

        Returns:
            List of PolicyDecision objects for the audit trail.
        """
        decisions = []
        for rule in self._rules:
            decision = rule.evaluate(draft, context)
            decisions.append(decision)
        return decisions
