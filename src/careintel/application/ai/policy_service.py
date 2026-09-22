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

import uuid
from typing import Any, Protocol

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
        for claim in draft.claim_provenance:
            for sid in claim.supporting_source_ids:
                if sid not in valid_ids:
                    invalid_citations.append(str(sid))

        if invalid_citations:
            return PolicyDecision(
                check_type=self.check_type,
                policy_version=self.version,
                outcome=PolicyOutcome.FAIL,
                detail={"invalid_source_ids": invalid_citations},
            )

        return PolicyDecision(
            check_type=self.check_type,
            policy_version=self.version,
            outcome=PolicyOutcome.PASS,
            detail={},
        )


class PolicyService:
    """
    Executes safety policies against an AI draft.
    """

    def __init__(self, rules: list[PolicyRule] | None = None) -> None:
        if rules is None:
            # Default safety suite
            self._rules: list[PolicyRule] = [ProvenanceIntegrityRule()]
        else:
            self._rules = rules

    def evaluate_draft(
        self, draft: AIDraft, context: SafeContext
    ) -> list[PolicyDecision]:
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
