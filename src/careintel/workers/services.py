"""Explicit application-service composition for Celery workers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.ai.ai_service import AIService
from careintel.application.ai.ai_workflow_service import AIWorkflowService
from careintel.application.ai.context_builder import AIContextBuilder
from careintel.application.ai.policy_service import PolicyService
from careintel.application.auth.consent_service import ConsentService
from careintel.application.case.case_service import CaseService
from careintel.application.handoff.handoff_service import HandoffService
from careintel.application.processing.access import ProcessingAccessGuard
from careintel.application.processing.document_processor import DocumentProcessor
from careintel.application.processing.extraction_processor import ExtractionProcessor
from careintel.application.processing.language_processor import LanguageProcessor
from careintel.application.processing.processing_service import ProcessingService
from careintel.application.processing.speech_processor import SpeechProcessor
from careintel.application.retrieval.retrieval_service import RetrievalService
from careintel.application.structuring.structuring_service import StructuringService
from careintel.application.workflow.task_service import AsyncTaskService
from careintel.core.config import Settings, get_settings
from careintel.infrastructure.reranker.noop_reranker import NoOpReranker
from careintel.persistence.repositories.ai_repo import AIRepository
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_history_repo import CaseHistoryRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.consent_repo import ConsentRepository
from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.handoff_repo import HandoffRepository
from careintel.persistence.repositories.knowledge_repo import KnowledgeRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository
from careintel.persistence.repositories.retrieval_repo import RetrievalRepository
from careintel.persistence.repositories.structuring_repo import StructuringRepository
from careintel.persistence.repositories.task_repo import AsyncTaskRepository
from careintel.persistence.repositories.text_content_repo import TextContentRepository
from careintel.workers.providers import WorkerProviders, get_worker_providers


def _consent(session: AsyncSession) -> ConsentService:
    return ConsentService(ConsentRepository(session), AuditRepository(session))


def build_case_service(session: AsyncSession) -> CaseService:
    return CaseService(
        CaseRepository(session),
        CaseHistoryRepository(session),
        CaseOutboxRepository(session),
        AuditRepository(session),
    )


async def build_processing_service(session: AsyncSession) -> ProcessingService:
    settings = get_settings()
    providers = await get_worker_providers()
    evidence_repo = EvidenceRepository(session)
    processing_repo = ProcessingRepository(session)
    outbox_repo = EvidenceOutboxRepository(session)
    guard = ProcessingAccessGuard(evidence_repo, CaseRepository(session), _consent(session))
    return ProcessingService(
        document_processor=DocumentProcessor(
            settings, guard, processing_repo, outbox_repo, providers.blob, providers.ocr
        ),
        speech_processor=SpeechProcessor(
            settings, guard, processing_repo, outbox_repo, providers.blob, providers.speech
        ),
        language_processor=LanguageProcessor(
            settings,
            guard,
            processing_repo,
            outbox_repo,
            providers.language,
            providers.translation,
        ),
        extraction_processor=ExtractionProcessor(
            settings, guard, processing_repo, outbox_repo, providers.extraction
        ),
        task_service=AsyncTaskService(AsyncTaskRepository(session)),
        evidence_repo=evidence_repo,
        case_repo=CaseRepository(session),
        outbox_repo=outbox_repo,
        processing_repo=processing_repo,
        text_repo=TextContentRepository(session),
        audit_repo=AuditRepository(session),
        access_guard=guard,
    )


async def build_retrieval_service(session: AsyncSession) -> RetrievalService:
    providers = await get_worker_providers()
    return RetrievalService(
        session,
        RetrievalRepository(session),
        KnowledgeRepository(session),
        CaseRepository(session),
        _consent(session),
        AuditRepository(session),
        providers.embedding,
        NoOpReranker(),
    )


async def build_ai_workflow_service(session: AsyncSession) -> AIWorkflowService:
    settings: Settings = get_settings()
    providers: WorkerProviders = await get_worker_providers()
    return AIWorkflowService(
        CaseRepository(session),
        _consent(session),
        AIContextBuilder(
            RetrievalRepository(session),
            KnowledgeRepository(session),
            EvidenceRepository(session),
            TextContentRepository(session),
            ProcessingRepository(session),
            StructuringRepository(session),
        ),
        AIService(
            session,
            AIRepository(session),
            AuditRepository(session),
            providers.llm,
            PolicyService(),
        ),
        settings,
    )


def build_structuring_service(session: AsyncSession) -> StructuringService:
    return StructuringService(
        StructuringRepository(session),
        ProcessingRepository(session),
        CaseRepository(session),
        CaseOutboxRepository(session),
        AuditRepository(session),
        _consent(session),
        get_settings(),
    )


def build_handoff_service(session: AsyncSession) -> HandoffService:
    return HandoffService(
        HandoffRepository(session),
        CaseRepository(session),
        CaseHistoryRepository(session),
        CaseOutboxRepository(session),
        _consent(session),
        AuditRepository(session),
    )
