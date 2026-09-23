"""
Extraction Processor.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from ulid import ULID

from careintel.application.processing.access import ProcessingAccessGuard
from careintel.core.config import Settings
from careintel.core.errors import ValidationError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.processing.processor_type import ProcessorType
from careintel.infrastructure.extraction.port import ExtractionProvider
from careintel.persistence.models.evidence import EvidenceOutboxORM
from careintel.persistence.models.processing import (
    ExtractedCandidateORM,
    ExtractionRunORM,
    ProcessingRunORM,
)
from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository


class ExtractionProcessor:
    """Orchestrates structured candidate extraction."""

    def __init__(
        self,
        settings: Settings,
        access_guard: ProcessingAccessGuard,
        processing_repo: ProcessingRepository,
        outbox_repo: EvidenceOutboxRepository,
        extraction_provider: ExtractionProvider,
    ) -> None:
        self.settings = settings
        self.access_guard = access_guard
        self.processing_repo = processing_repo
        self.outbox_repo = outbox_repo
        self.extraction_provider = extraction_provider
        self.logger = logging.getLogger(__name__)

    async def process(
        self,
        evidence_id: uuid.UUID,
        source_processing_run_id: uuid.UUID,
        text: str,
        user: UserContext,
        correlation_id: str,
    ) -> uuid.UUID:
        """
        Executes Extraction Pipeline for given text.
        """
        evidence = await self.access_guard.require_ready_evidence(evidence_id, user)
        source_run = await self.processing_repo.get_run_by_id(source_processing_run_id)
        if (
            source_run is None
            or source_run.evidence_id != evidence_id
            or source_run.status != ProcessingStatus.COMPLETED.value
        ):
            raise ValidationError("Extraction source processing run is invalid or incomplete.")
        if not text.strip():
            raise ValidationError("Extraction source artifact contains no readable text.")

        config_version = f"v1:{source_processing_run_id}"
        existing_run = await self.processing_repo.get_run_by_idempotency_key(
            evidence_id=evidence_id,
            processor_type=ProcessorType.CANDIDATE_EXTRACTION.value,
            config_version=config_version,
        )
        if existing_run:
            return existing_run.id

        run_id = uuid.uuid4()
        run = ProcessingRunORM(
            id=run_id,
            evidence_id=evidence_id,
            processor_type=ProcessorType.CANDIDATE_EXTRACTION.value,
            provider=self.settings.extraction_provider,
            status=ProcessingStatus.PENDING.value,
            config_version=config_version,
            started_at=datetime.now(UTC).replace(tzinfo=None),
        )
        await self.processing_repo.add_run(run)
        run.status = ProcessingStatus.RUNNING.value

        try:
            extraction_result = await self.extraction_provider.extract_candidates(
                text, str(run_id), evidence_id
            )

            ext_run = ExtractionRunORM(
                id=uuid.uuid4(),
                processing_run_id=run_id,
                source_processing_run_id=source_processing_run_id,
                provider_version=extraction_result.provider_version,
            )
            self.processing_repo.session.add(ext_run)
            await self.processing_repo.session.flush()

            for candidate in extraction_result.candidates:
                if candidate.run_id != run_id:
                    raise ValidationError("Candidate extraction run identity does not match.")
                if not candidate.provenance:
                    raise ValidationError("Extracted candidate has no provenance.")

                prov_dicts = []
                for p in candidate.provenance:
                    if p.evidence_id != evidence_id:
                        raise ValidationError(
                            "Candidate provenance references another evidence item."
                        )
                    if (p.span_start is None) != (p.span_end is None):
                        raise ValidationError("Candidate provenance has an incomplete text span.")
                    if p.span_start is not None and p.span_end is not None:
                        if p.span_start < 0 or p.span_end <= p.span_start or p.span_end > len(text):
                            raise ValidationError("Candidate provenance text span is invalid.")
                        source_slice = text[p.span_start : p.span_end]
                        if p.raw_source_text is not None and p.raw_source_text != source_slice:
                            raise ValidationError(
                                "Candidate provenance text does not match source."
                            )
                    prov_dicts.append(
                        {
                            "evidence_id": str(p.evidence_id),
                            "page_number": p.page_number,
                            "region_id": str(p.region_id) if p.region_id else None,
                            "segment_id": str(p.segment_id) if p.segment_id else None,
                            "span_start": p.span_start,
                            "span_end": p.span_end,
                            "raw_source_text": p.raw_source_text,
                        }
                    )

                cand_orm = ExtractedCandidateORM(
                    id=candidate.candidate_id,
                    extraction_run_id=ext_run.id,
                    field_type=candidate.field_type,
                    value=candidate.value,
                    normalized_value=candidate.normalized_value,
                    confidence=candidate.confidence,
                    status=candidate.status,
                    provenance_json=prov_dicts,
                )
                self.processing_repo.session.add(cand_orm)

            await self.processing_repo.session.flush()

            run.status = ProcessingStatus.COMPLETED.value
            run.completed_at = datetime.now(UTC).replace(tzinfo=None)

        except Exception as exc:
            self.logger.error(
                "Extraction processing failed",
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
                "processor_type": ProcessorType.CANDIDATE_EXTRACTION.value,
                "status": run.status,
            },
        )
        await self.outbox_repo.append(outbox_event)

        return run_id
