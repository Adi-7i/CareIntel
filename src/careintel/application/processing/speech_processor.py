"""
Audio / STT Pipeline Processor.
"""

from __future__ import annotations

import logging
import os
import tempfile
import uuid
from datetime import UTC, datetime

from ulid import ULID

from careintel.core.config import Settings
from careintel.core.errors import (
    AuthorizationError,
    CareIntelError,
    NotFoundError,
)
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.evidence.states import EvidenceState
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.processing.processor_type import ProcessorType
from careintel.infrastructure.storage.port import BlobStoragePort
from careintel.infrastructure.stt.port import SpeechProvider
from careintel.persistence.models.evidence import EvidenceOutboxORM
from careintel.persistence.models.processing import (
    ProcessingRunORM,
    TranscriptRunORM,
    TranscriptSegmentORM,
)
from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository


class SpeechProcessor:
    """Orchestrates the Audio / STT pipeline."""

    def __init__(
        self,
        settings: Settings,
        evidence_repo: EvidenceRepository,
        processing_repo: ProcessingRepository,
        outbox_repo: EvidenceOutboxRepository,
        blob_storage: BlobStoragePort,
        speech_provider: SpeechProvider,
    ) -> None:
        self.settings = settings
        self.evidence_repo = evidence_repo
        self.processing_repo = processing_repo
        self.outbox_repo = outbox_repo
        self.blob_storage = blob_storage
        self.speech_provider = speech_provider
        self.logger = logging.getLogger(__name__)

    async def process(
        self, evidence_id: uuid.UUID, user: UserContext, correlation_id: str
    ) -> uuid.UUID:
        """
        Executes the Audio STT pipeline for a given evidence ID.
        Returns the ProcessingRun ID.
        """
        # 1. Fetch Evidence
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise NotFoundError(f"Evidence {evidence_id} not found.")

        # 2. Authorization
        if not AuthorizationPolicy.evaluate(
            user, Permission.PROCESSING_WRITE, str(evidence.case_id)
        ):
            raise AuthorizationError("Missing PROCESSING_WRITE permission for this case.")

        # 3. Consent Re-check
        if evidence.state != EvidenceState.READY:
            raise CareIntelError(
                f"Evidence must be READY for processing. Current: {evidence.state}"
            )

        if evidence.modality != EvidenceModality.AUDIO:
            raise CareIntelError(f"SpeechProcessor cannot handle modality: {evidence.modality}")

        # 4. Idempotency Check
        config_version = "v1"
        existing_run = await self.processing_repo.get_run_by_idempotency_key(
            evidence_id=evidence_id,
            processor_type=ProcessorType.SPEECH_TRANSCRIPTION.value,
            config_version=config_version,
        )
        if existing_run and existing_run.status in (
            ProcessingStatus.COMPLETED,
            ProcessingStatus.RUNNING,
        ):
            return existing_run.id

        # 5. Create Run Record
        run_id = uuid.uuid4()
        run = ProcessingRunORM(
            id=run_id,
            evidence_id=evidence_id,
            processor_type=ProcessorType.SPEECH_TRANSCRIPTION.value,
            provider=self.settings.stt_provider,
            status=ProcessingStatus.RUNNING.value,
            config_version=config_version,
            started_at=datetime.now(UTC),
        )
        await self.processing_repo.add_run(run)

        # 6. Execute STT in Temp File
        fd, local_file_path = tempfile.mkstemp(prefix=f"stt_{run_id}_")

        try:
            # Download blob
            if not evidence.storage_key:
                raise CareIntelError("Evidence missing storage_key")

            with os.fdopen(fd, "wb") as f:
                async for chunk in self.blob_storage.download(evidence.storage_key):
                    f.write(chunk)

            # STT processing
            stt_result = await self.speech_provider.process_audio(local_file_path, str(run_id))

            # Persist output
            transcript_run = TranscriptRunORM(
                id=uuid.uuid4(),
                processing_run_id=run_id,
                provider_version=stt_result.provider_version,
            )
            # Add transcript run to session
            self.processing_repo.session.add(transcript_run)

            for segment in stt_result.segments:
                segment_orm = TranscriptSegmentORM(
                    id=segment.segment_id,
                    transcript_run_id=transcript_run.id,
                    start_time_ms=segment.start_time_ms,
                    end_time_ms=segment.end_time_ms,
                    text_content=segment.text,
                    language=segment.language,
                    confidence=segment.confidence,
                    speaker_label=segment.speaker_label,
                    is_silence=segment.is_silence,
                )
                self.processing_repo.session.add(segment_orm)

            await self.processing_repo.session.flush()

            run.status = ProcessingStatus.COMPLETED.value
            run.completed_at = datetime.now(UTC)

        except Exception as e:
            self.logger.error(f"STT Pipeline failed for run {run_id}: {e}")
            run.status = ProcessingStatus.FAILED.value
            run.failure_reason = str(e)
            run.completed_at = datetime.now(UTC)

        finally:
            if os.path.exists(local_file_path):
                os.remove(local_file_path)

        # 7. Emit Outbox Event
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
                "processor_type": ProcessorType.SPEECH_TRANSCRIPTION.value,
                "status": run.status,
            },
        )
        await self.outbox_repo.append(outbox_event)

        return run_id
