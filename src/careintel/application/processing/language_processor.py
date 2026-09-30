"""
Language Normalization and Translation Processor.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from ulid import ULID

from careintel.application.processing.access import ProcessingAccessGuard
from careintel.core.config import Settings
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.processing.processor_type import ProcessorType
from careintel.infrastructure.language.port import LanguageProvider
from careintel.infrastructure.translation.port import TranslationProvider
from careintel.persistence.models.evidence import EvidenceOutboxORM
from careintel.persistence.models.processing import (
    LanguageResultORM,
    ProcessingRunORM,
)
from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository


class LanguageProcessor:
    """Orchestrates Language Detection and Translation."""

    def __init__(
        self,
        settings: Settings,
        access_guard: ProcessingAccessGuard,
        processing_repo: ProcessingRepository,
        outbox_repo: EvidenceOutboxRepository,
        language_provider: LanguageProvider,
        translation_provider: TranslationProvider,
    ) -> None:
        self.settings = settings
        self.access_guard = access_guard
        self.processing_repo = processing_repo
        self.outbox_repo = outbox_repo
        self.language_provider = language_provider
        self.translation_provider = translation_provider
        self.logger = logging.getLogger(__name__)

    async def process(
        self,
        evidence_id: uuid.UUID,
        text: str,
        user: UserContext,
        correlation_id: str,
        target_language: str = "en",
    ) -> uuid.UUID:
        """
        Executes Language Pipeline for given text.
        """
        evidence = await self.access_guard.require_ready_evidence(evidence_id, user)

        config_version = "v1"
        existing_run = await self.processing_repo.get_run_by_idempotency_key(
            evidence_id=evidence_id,
            processor_type=ProcessorType.LANGUAGE_NORMALIZATION.value,
            config_version=config_version,
        )
        if existing_run:
            return existing_run.id

        run_id = uuid.uuid4()
        run = ProcessingRunORM(
            id=run_id,
            evidence_id=evidence_id,
            processor_type=ProcessorType.LANGUAGE_NORMALIZATION.value,
            provider=self.settings.language_detection_provider,
            status=ProcessingStatus.PENDING.value,
            config_version=config_version,
            started_at=datetime.now(UTC).replace(tzinfo=None),
        )
        await self.processing_repo.add_run(run)
        run.status = ProcessingStatus.RUNNING.value

        try:
            detections = await self.language_provider.detect_language(text)
            detected_lang = detections[0].language if detections else None
            detected_conf = detections[0].confidence if detections else None

            translation_text = None
            trans_provider = None

            if detected_lang and detected_lang != target_language:
                translation_text = await self.translation_provider.translate(
                    text, detected_lang, target_language
                )
                trans_provider = self.settings.translation_provider

            result_orm = LanguageResultORM(
                id=uuid.uuid4(),
                processing_run_id=run_id,
                detected_language=detected_lang,
                detected_confidence=detected_conf,
                normalized_text=text,
                translation_text=translation_text,
                translation_provider=trans_provider,
            )
            self.processing_repo.session.add(result_orm)
            await self.processing_repo.session.flush()

            run.status = ProcessingStatus.COMPLETED.value
            run.completed_at = datetime.now(UTC).replace(tzinfo=None)

        except Exception as exc:
            self.logger.error(
                "Language processing failed",
                extra={"run_id": str(run_id), "error_type": type(exc).__name__},
            )
            run.status = ProcessingStatus.FAILED.value
            run.failure_reason = type(exc).__name__
            run.completed_at = datetime.now(UTC).replace(tzinfo=None)

        outbox_event = EvidenceOutboxORM(
            id=str(ULID()),
            event_type=(
                AuditEventType.PROCESSING_COMPLETED.value
                if run.status == ProcessingStatus.COMPLETED.value
                else AuditEventType.PROCESSING_FAILED.value
            ),
            event_version=1,
            producer="careintel.processing",
            correlation_id=correlation_id,
            evidence_id=evidence_id,
            case_id=evidence.case_id,
            actor_id=user.id,
            payload={
                "run_id": str(run_id),
                "processor_type": ProcessorType.LANGUAGE_NORMALIZATION.value,
                "status": run.status,
            },
        )
        await self.outbox_repo.append(outbox_event)

        return run_id
