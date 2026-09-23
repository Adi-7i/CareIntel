"""Authorized application boundary for case-scoped advisory AI execution."""

from __future__ import annotations

import uuid

from careintel.application.ai.ai_service import AIService
from careintel.application.ai.context_builder import AIContextBuilder
from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.core.config import Settings
from careintel.core.errors import NotFoundError
from careintel.domain.ai.models import AIDraft, AITaskConfig
from careintel.domain.ai.status import TaskType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.persistence.repositories.case_repo import CaseRepository


class AIWorkflowService:
    """Builds context from persisted state before invoking the AI orchestrator."""

    def __init__(
        self,
        case_repo: CaseRepository,
        consent_service: ConsentService,
        context_builder: AIContextBuilder,
        ai_service: AIService,
        settings: Settings,
    ) -> None:
        self._cases = case_repo
        self._consent = consent_service
        self._context_builder = context_builder
        self._ai = ai_service
        self._settings = settings

    async def execute_advisory(
        self,
        actor: UserContext,
        case_id: uuid.UUID,
        retrieval_run_id: uuid.UUID,
        task_type: TaskType,
    ) -> AIDraft:
        case = await self._cases.get_by_id(case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        PermissionService.check(
            actor,
            Permission.AI_WRITE,
            facility_scope=case.facility_id,
        )
        await self._consent.require_active(
            case.synthetic_subject_id,
            ConsentPurpose.AI_ANALYSIS.value,
            "1.0",
        )
        context = await self._context_builder.build(case_id, retrieval_run_id, task_type)
        config = AITaskConfig(
            task_type=task_type,
            provider=self._settings.llm_provider,
            model=(
                self._settings.azure_llm_deployment
                if self._settings.llm_provider == "azure_openai"
                else "demo"
            ),
            prompt_version="careintel-advisory-v1",
            schema_version="advisory-output-v1",
            timeout_seconds=self._settings.llm_timeout_seconds,
        )
        return await self._ai.execute_task(actor, case_id, config, context)
