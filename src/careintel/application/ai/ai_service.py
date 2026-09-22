"""
AI Service.

Orchestrates AI task execution, validation, policy enforcement,
and human-in-the-loop draft review.

CRITICAL INVARIANTS:
- All LLM inputs must be encapsulated in a SafeContext.
- LLM outputs are always treated as drafts awaiting human review.
- PolicyService must be executed on all drafts.
- A failed policy check automatically rejects the draft.
"""

from __future__ import annotations

import datetime
import hashlib
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.ai.policy_service import PolicyService
from careintel.core.correlation import get_correlation_id
from careintel.core.errors import NotFoundError, ValidationError
from careintel.domain.ai.models import AIDraft, AITaskConfig, SafeContext
from careintel.domain.ai.status import (
    AIRunStatus,
    DraftReviewerStatus,
    PolicyOutcome,
    ValidationStatus,
)
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.infrastructure.ai.port import LLMProvider, LLMProviderError
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.repositories.ai_repo import AIRepository
from careintel.persistence.repositories.audit_repo import AuditRepository


class AIService:
    """Orchestrates AI workflows and safety enforcement."""

    def __init__(
        self,
        session: AsyncSession,
        ai_repo: AIRepository,
        audit_repo: AuditRepository,
        llm_provider: LLMProvider,
        policy_service: PolicyService,
    ) -> None:
        self._session = session
        self._repo = ai_repo
        self._audit = audit_repo
        self._llm = llm_provider
        self._policy = policy_service

    async def _audit_event(
        self,
        event_type: AuditEventType,
        actor_id: uuid.UUID,
        target_id: uuid.UUID | None,
        target_type: str | None,
        outcome: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        entry = AuditLogORM(
            event_type=event_type.value,
            actor_id=actor_id,
            target_id=target_id,
            target_type=target_type,
            correlation_id=get_correlation_id(),
            outcome=outcome,
            detail=detail,
        )
        await self._audit.append(entry)

    def _hash_context(self, context: SafeContext) -> str:
        """Deterministically hash the context for idempotency."""
        # Simple representation for hashing; in production, use a stable JSON dump
        # covering the exact fields.
        rep = (
            context.system_instructions
            + context.task_instructions
            + str(context.knowledge_passages)
            + str(context.patient_evidence)
            + str(context.stt_transcripts)
            + str(context.ocr_content)
        )
        return hashlib.sha256(rep.encode("utf-8")).hexdigest()

    async def execute_task(
        self,
        actor: UserContext,
        case_id: uuid.UUID,
        config: AITaskConfig,
        context: SafeContext,
    ) -> AIDraft:
        """
        Execute an AI task using the provided SafeContext and Config.
        """
        from careintel.application.auth.permission_service import PermissionService

        PermissionService.check(actor, Permission.AI_WRITE)

        input_hash = self._hash_context(context)
        ret_meta = context.retrieval_metadata
        retrieval_id = ret_meta.retrieval_run_id if ret_meta else None

        # 1. Idempotency Check
        existing_run = await self._repo.get_run_by_idempotency_key(
            case_id=case_id,
            task_type=config.task_type.value,
            input_hash=input_hash,
            prompt_version=config.prompt_version,
        )
        if existing_run is not None:
            # If completed and draft exists, return the cached draft
            draft_orm = await self._repo.get_draft_for_run(existing_run.id)
            if draft_orm:
                return self._to_draft_domain(draft_orm)

        # 2. Create Run Record
        run_orm = await self._repo.create_run(
            {
                "case_id": case_id,
                "actor_id": actor.id,
                "task_type": config.task_type.value,
                "provider": config.provider,
                "model": config.model,
                "prompt_version": config.prompt_version,
                "schema_version": config.schema_version,
                "retrieval_run_id": retrieval_id,
                "status": AIRunStatus.IN_PROGRESS.value,
                "input_hash": input_hash,
                "usage_json": {},
            }
        )
        await self._session.commit()
        await self._audit_event(
            event_type=AuditEventType.AI_RUN_STARTED,
            actor_id=actor.id,
            target_id=run_orm.id,
            target_type="ai_run",
            outcome="success",
        )

        # 3. Invoke LLM
        try:
            result = await self._llm.generate_structured(context, config)
        except LLMProviderError as e:
            await self._repo.update_run(
                run_orm.id,
                {
                    "status": AIRunStatus.FAILED.value,
                    "error_category": "PROVIDER_ERROR",
                    "failure_reason": str(e),
                },
            )
            await self._session.commit()
            await self._audit_event(
                event_type=AuditEventType.AI_RUN_FAILED,
                actor_id=actor.id,
                target_id=run_orm.id,
                target_type="ai_run",
                outcome="failure",
                detail={"error": str(e)},
            )
            raise

        output_hash = hashlib.sha256(result.raw_response.encode("utf-8")).hexdigest()
        usage = {
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.prompt_tokens + result.completion_tokens,
        }

        if not result.parsed_content:
            # Validation failure at the adapter level
            # (should not happen with structured outputs, but just in case)
            await self._repo.update_run(
                run_orm.id,
                {
                    "status": AIRunStatus.FAILED.value,
                    "output_hash": output_hash,
                    "usage_json": usage,
                    "error_category": "VALIDATION_ERROR",
                    "failure_reason": "Failed to parse JSON response",
                },
            )
            await self._session.commit()
            raise ValueError("Failed to parse LLM structured output.")

        # 4. Create initial Draft
        draft_content = result.parsed_content
        # Extract provenance if the schema supports it
        claim_provenance_raw = draft_content.get("claim_provenance", [])

        draft_orm = await self._repo.create_draft(
            {
                "ai_run_id": run_orm.id,
                "content_json": draft_content,
                "validation_status": ValidationStatus.ACCEPTED.value,
                "validation_errors": [],
                "provenance_json": (
                    claim_provenance_raw if isinstance(claim_provenance_raw, list) else []
                ),
                "reviewer_status": DraftReviewerStatus.DRAFT.value,
            }
        )
        draft_domain = self._to_draft_domain(draft_orm)

        # 5. Execute Deterministic Safety Policies
        policy_decisions = self._policy.evaluate_draft(draft_domain, context)

        await self._repo.create_policy_decisions(
            [
                {
                    "ai_run_id": run_orm.id,
                    "check_type": d.check_type.value,
                    "policy_version": d.policy_version,
                    "outcome": d.outcome.value,
                    "detail_json": d.detail,
                }
                for d in policy_decisions
            ]
        )

        has_failure = any(d.outcome == PolicyOutcome.FAIL for d in policy_decisions)

        # 6. Finalize Run Status
        final_run_status = AIRunStatus.COMPLETED
        final_reviewer_status = DraftReviewerStatus.DRAFT

        if has_failure:
            final_run_status = AIRunStatus.POLICY_BLOCKED
            final_reviewer_status = DraftReviewerStatus.REJECTED

        await self._repo.update_run(
            run_orm.id,
            {
                "status": final_run_status.value,
                "output_hash": output_hash,
                "usage_json": usage,
            },
        )

        if has_failure:
            await self._repo.update_draft(
                draft_orm.id, {"reviewer_status": final_reviewer_status.value}
            )

        await self._session.commit()

        # Emit audit events
        if has_failure:
            await self._audit_event(
                event_type=AuditEventType.AI_POLICY_BLOCKED,
                actor_id=actor.id,
                target_id=run_orm.id,
                target_type="ai_run",
                outcome="success",
            )
        else:
            await self._audit_event(
                event_type=AuditEventType.AI_RUN_COMPLETED,
                actor_id=actor.id,
                target_id=run_orm.id,
                target_type="ai_run",
                outcome="success",
            )

        # Re-fetch draft to return updated domain object
        updated_draft = await self._repo.get_draft(draft_orm.id)
        assert updated_draft is not None
        return self._to_draft_domain(updated_draft)

    async def approve_draft(self, actor: UserContext, draft_id: uuid.UUID) -> None:
        """Approve an AI draft for use in case state transitions."""
        from careintel.application.auth.permission_service import PermissionService

        PermissionService.check(actor, Permission.AI_WRITE)

        draft = await self._repo.get_draft(draft_id)
        if not draft:
            raise NotFoundError("Draft not found")

        if draft.reviewer_status == DraftReviewerStatus.REJECTED.value:
            raise ValidationError("Cannot approve a rejected draft.")

        await self._repo.update_draft(
            draft_id,
            {
                "reviewer_status": DraftReviewerStatus.APPROVED.value,
                "reviewer_id": actor.id,
                "reviewed_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            },
        )
        await self._session.commit()
        await self._audit_event(
            event_type=AuditEventType.AI_DRAFT_REVIEWED,
            actor_id=actor.id,
            target_id=draft_id,
            target_type="ai_draft",
            outcome="success",
            detail={"decision": "APPROVED"},
        )

    async def reject_draft(self, actor: UserContext, draft_id: uuid.UUID) -> None:
        """Reject an AI draft."""
        from careintel.application.auth.permission_service import PermissionService

        PermissionService.check(actor, Permission.AI_WRITE)

        draft = await self._repo.get_draft(draft_id)
        if not draft:
            raise NotFoundError("Draft not found")

        await self._repo.update_draft(
            draft_id,
            {
                "reviewer_status": DraftReviewerStatus.REJECTED.value,
                "reviewer_id": actor.id,
                "reviewed_at": datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            },
        )
        await self._session.commit()
        await self._audit_event(
            event_type=AuditEventType.AI_DRAFT_REJECTED,
            actor_id=actor.id,
            target_id=draft_id,
            target_type="ai_draft",
            outcome="success",
            detail={"decision": "REJECTED"},
        )

    @staticmethod
    def _to_draft_domain(orm: Any) -> AIDraft:
        from careintel.domain.ai.models import ClaimProvenance

        prov_list = []
        for p in orm.provenance_json:
            src_ids = p.get("supporting_source_ids", [])
            ids = [uuid.UUID(uid) if isinstance(uid, str) else uid for uid in src_ids]
            prov_list.append(
                ClaimProvenance(
                    claim_text=p.get("claim_text", ""),
                    status=p.get("status", "UNSUPPORTED"),
                    supporting_source_ids=ids,
                )
            )

        return AIDraft(
            draft_id=orm.id,
            ai_run_id=orm.ai_run_id,
            content=dict(orm.content_json),
            validation_status=ValidationStatus(orm.validation_status),
            validation_errors=[],  # Simplification for this phase
            claim_provenance=prov_list,
            reviewer_status=DraftReviewerStatus(orm.reviewer_status),
            reviewer_id=orm.reviewer_id,
            reviewed_at=orm.reviewed_at,
            created_at=orm.created_at,
        )
