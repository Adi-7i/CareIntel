"""
Processing Orchestration Service.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

from careintel.application.processing.access import ProcessingAccessGuard
from careintel.application.processing.document_processor import DocumentProcessor
from careintel.application.processing.extraction_processor import ExtractionProcessor
from careintel.application.processing.language_processor import LanguageProcessor
from careintel.application.processing.speech_processor import SpeechProcessor
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.processing.processing_commands import TriggerProcessingCommand
from careintel.domain.processing.processing_models import ProcessingRunRecord
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.processing.processor_type import ProcessorType

if TYPE_CHECKING:
    from careintel.application.workflow.task_service import AsyncTaskService
    from careintel.persistence.repositories.audit_repo import AuditRepository
    from careintel.persistence.repositories.case_repo import CaseRepository
    from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
    from careintel.persistence.repositories.evidence_repo import EvidenceRepository
    from careintel.persistence.repositories.processing_repo import ProcessingRepository
    from careintel.persistence.repositories.text_content_repo import TextContentRepository


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
        case_repo: CaseRepository,
        outbox_repo: EvidenceOutboxRepository,
        processing_repo: ProcessingRepository,
        text_repo: TextContentRepository,
        audit_repo: AuditRepository,
        access_guard: ProcessingAccessGuard,
    ) -> None:
        self.document_processor = document_processor
        self.speech_processor = speech_processor
        self.language_processor = language_processor
        self.extraction_processor = extraction_processor
        self.task_service = task_service
        self.evidence_repo = evidence_repo
        self.case_repo = case_repo
        self.outbox_repo = outbox_repo
        self.processing_repo = processing_repo
        self.text_repo = text_repo
        self.audit_repo = audit_repo
        self.access_guard = access_guard
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

        evidence = await self.access_guard.require_ready_evidence(command.evidence_id, user)

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
        task_name = task_name_map.get(
            command.processor_type, "careintel.tasks.processing.run_processing"
        )

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

    @staticmethod
    def _to_domain(run: Any) -> ProcessingRunRecord:
        return ProcessingRunRecord(
            run_id=run.id,
            evidence_id=run.evidence_id,
            processor_type=ProcessorType(run.processor_type),
            provider=run.provider,
            status=ProcessingStatus(run.status),
            config_version=run.config_version,
            started_at=run.started_at,
            completed_at=run.completed_at,
            failure_reason=run.failure_reason,
        )

    @staticmethod
    def _source_run_id(parameters: dict[str, Any]) -> uuid.UUID:
        from careintel.core.errors import ValidationError

        raw = parameters.get("source_processing_run_id")
        if raw is None:
            raise ValidationError("source_processing_run_id is required.")
        try:
            return raw if isinstance(raw, uuid.UUID) else uuid.UUID(str(raw))
        except (TypeError, ValueError) as exc:
            raise ValidationError("source_processing_run_id must be a UUID.") from exc

    async def _text_from_source_run(self, evidence_id: uuid.UUID, source_run_id: uuid.UUID) -> str:
        from careintel.core.errors import ValidationError

        source = await self.processing_repo.get_run_by_id(source_run_id)
        if (
            source is None
            or source.evidence_id != evidence_id
            or source.status != ProcessingStatus.COMPLETED.value
        ):
            raise ValidationError("Source processing run is invalid or incomplete.")

        if source.processor_type == ProcessorType.DOCUMENT_OCR.value:
            regions = await self.processing_repo.get_ocr_regions_for_run(source_run_id)
            source_text = "\n".join(region.text_content for region in regions)
        elif source.processor_type == ProcessorType.SPEECH_TRANSCRIPTION.value:
            segments = await self.processing_repo.get_transcript_segments_for_run(source_run_id)
            source_text = "\n".join(
                segment.text_content for segment in segments if not segment.is_silence
            )
        elif source.processor_type == ProcessorType.LANGUAGE_NORMALIZATION.value:
            result = await self.processing_repo.get_language_result(source_run_id)
            source_text = (
                "" if result is None else result.translation_text or result.normalized_text
            )
        else:
            raise ValidationError("Processing run is not a supported text source.")

        if not source_text.strip():
            raise ValidationError("Source processing run contains no readable text.")
        return source_text

    async def execute_processing(
        self, command: TriggerProcessingCommand, user: UserContext, correlation_id: str
    ) -> ProcessingRunRecord:
        """Execute one processing step synchronously through the application boundary."""
        evidence = await self.access_guard.require_ready_evidence(command.evidence_id, user)

        if command.processor_type == ProcessorType.DOCUMENT_OCR:
            run_id = await self.document_processor.process(evidence.id, user, correlation_id)
        elif command.processor_type == ProcessorType.SPEECH_TRANSCRIPTION:
            run_id = await self.speech_processor.process(evidence.id, user, correlation_id)
        elif command.processor_type == ProcessorType.LANGUAGE_NORMALIZATION:
            if evidence.modality == EvidenceModality.TEXT.value:
                text_record = await self.text_repo.get_for_evidence(evidence.id)
                if text_record is None:
                    from careintel.core.errors import ValidationError

                    raise ValidationError("Text evidence has no immutable text artifact.")
                source_text = text_record.content
            else:
                source_run_id = self._source_run_id(command.parameters)
                source_text = await self._text_from_source_run(evidence.id, source_run_id)
            run_id = await self.language_processor.process(
                evidence.id,
                source_text,
                user,
                correlation_id,
                target_language=str(command.parameters.get("target_language", "en")),
            )
        elif command.processor_type == ProcessorType.CANDIDATE_EXTRACTION:
            source_run_id = self._source_run_id(command.parameters)
            source_text = await self._text_from_source_run(evidence.id, source_run_id)
            run_id = await self.extraction_processor.process(
                evidence.id,
                source_run_id,
                source_text,
                user,
                correlation_id,
            )
        else:  # pragma: no cover - enum exhaustiveness guard
            from careintel.core.errors import ValidationError

            raise ValidationError("Unsupported processor type.")

        run = await self.processing_repo.get_run_by_id(run_id)
        if run is None:
            from careintel.core.errors import NotFoundError

            raise NotFoundError("Processing run was not persisted.")

        from careintel.persistence.models.audit import AuditLogORM

        await self.audit_repo.append(
            AuditLogORM(
                event_type=(
                    AuditEventType.PROCESSING_COMPLETED.value
                    if run.status == ProcessingStatus.COMPLETED.value
                    else AuditEventType.PROCESSING_FAILED.value
                ),
                actor_id=user.id,
                target_id=run.id,
                target_type="processing_run",
                correlation_id=correlation_id,
                outcome=(
                    "SUCCESS" if run.status == ProcessingStatus.COMPLETED.value else "FAILURE"
                ),
                detail={
                    "evidence_id": str(evidence.id),
                    "processor_type": run.processor_type,
                    "status": run.status,
                },
            )
        )
        return self._to_domain(run)

    async def get_run(self, run_id: uuid.UUID, user: UserContext) -> ProcessingRunRecord:
        from careintel.core.errors import NotFoundError

        run = await self.processing_repo.get_run_by_id(run_id)
        if run is None:
            raise NotFoundError("Processing run not found.")
        await self.access_guard.require_readable_evidence(run.evidence_id, user)
        return self._to_domain(run)
