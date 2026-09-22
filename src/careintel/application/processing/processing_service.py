"""
Processing Orchestration Service.
"""

from __future__ import annotations

import logging
import uuid

from careintel.application.processing.document_processor import DocumentProcessor
from careintel.application.processing.extraction_processor import ExtractionProcessor
from careintel.application.processing.language_processor import LanguageProcessor
from careintel.application.processing.speech_processor import SpeechProcessor
from careintel.domain.auth.models import UserContext
from careintel.domain.processing.processing_commands import TriggerProcessingCommand
from careintel.domain.processing.processor_type import ProcessorType


class ProcessingService:
    """Orchestrates different multimodal processing pipelines."""

    def __init__(
        self,
        document_processor: DocumentProcessor,
        speech_processor: SpeechProcessor,
        language_processor: LanguageProcessor,
        extraction_processor: ExtractionProcessor,
        task_service: AsyncTaskService,
        evidence_repo: EvidenceRepository,
        outbox_repo: EvidenceOutboxRepository,
    ) -> None:
        self.document_processor = document_processor
        self.speech_processor = speech_processor
        self.language_processor = language_processor
        self.extraction_processor = extraction_processor
        self.task_service = task_service
        self.evidence_repo = evidence_repo
        self.outbox_repo = outbox_repo
        self.logger = logging.getLogger(__name__)

    async def trigger_processing(
        self, command: TriggerProcessingCommand, user: UserContext, correlation_id: str
    ) -> uuid.UUID:
        """
        Triggers the appropriate processing pipeline by writing an outbox event
        and creating a PENDING async task.
        Returns the async task ID.
        """
        self.logger.info(
            f"Dispatching {command.processor_type} processing for evidence {command.evidence_id}"
        )

        evidence = await self.evidence_repo.get_by_id(command.evidence_id)
        if not evidence:
            from careintel.core.errors import NotFoundError
            raise NotFoundError("Evidence not found")

        # 1. Create outbox event
        import datetime

        from ulid import ULID

        from careintel.persistence.models.evidence import EvidenceOutboxORM

        now = datetime.datetime.now(datetime.UTC)
        outbox_event = EvidenceOutboxORM(
            id=str(ULID()),
            event_type="EVIDENCE_PROCESSING_REQUESTED",
            event_version=1,
            occurred_at=now,
            producer="careintel.processing_service",
            correlation_id=correlation_id,
            evidence_id=command.evidence_id,
            case_id=evidence.case_id,
            actor_id=user.id,
            payload={
                "processor_type": command.processor_type,
                "config_version": command.parameters.get("config_version", "v1"),
                **command.parameters,
            },
        )
        await self.outbox_repo.append(outbox_event)

        # 2. Create Task payload directly
        from careintel.domain.workflow.models import AsyncTaskPayload

        task_name_map = {
            ProcessorType.DOCUMENT_OCR.value: "careintel.tasks.processing.run_processing",
            ProcessorType.SPEECH_TRANSCRIPTION.value: "careintel.tasks.processing.run_processing",
            ProcessorType.LANGUAGE_NORMALIZATION.value: "careintel.tasks.processing.run_processing",
            ProcessorType.CANDIDATE_EXTRACTION.value: "careintel.tasks.processing.run_processing",
        }
        task_name = task_name_map.get(command.processor_type, "careintel.tasks.processing.run_processing")

        payload = AsyncTaskPayload(
            task_type=task_name,
            task_version=1,
            entity_type="evidence",
            entity_id=command.evidence_id,
            case_id=evidence.case_id,
            actor_id=user.id,
            correlation_id=correlation_id,
            config=outbox_event.payload,
        )

        task = await self.task_service.get_or_create_task(
            idempotency_key=f"outbox_{outbox_event.id}",
            payload=payload,
            causation_id=outbox_event.id,
        )

        return task.id

