"""
Extraction Processor.
"""

from __future__ import annotations

import logging
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
from careintel.domain.evidence.states import EvidenceState
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
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository


class ExtractionProcessor:
    """Orchestrates structured candidate extraction."""

    def __init__(
        self,
        settings: Settings,
        evidence_repo: EvidenceRepository,
        processing_repo: ProcessingRepository,
        outbox_repo: EvidenceOutboxRepository,
        extraction_provider: ExtractionProvider,
    ) -> None:
        self.settings = settings
        self.evidence_repo = evidence_repo
        self.processing_repo = processing_repo
        self.outbox_repo = outbox_repo
        self.extraction_provider = extraction_provider
        self.logger = logging.getLogger(__name__)

    async def process(
        self,
        evidence_id: uuid.UUID,
        text: str,
        user: UserContext,
        correlation_id: str,
    ) -> uuid.UUID:
        """
        Executes Extraction Pipeline for given text.
        """
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise NotFoundError(f"Evidence {evidence_id} not found.")

        if not AuthorizationPolicy.evaluate(
            user, Permission.PROCESSING_WRITE, str(evidence.case_id)
        ):
            raise AuthorizationError("Missing PROCESSING_WRITE permission for this case.")

        if evidence.state != EvidenceState.READY:
            raise CareIntelError(
                f"Evidence must be READY for processing. Current: {evidence.state}"
            )

        config_version = "v1"
        existing_run = await self.processing_repo.get_run_by_idempotency_key(
            evidence_id=evidence_id,
            processor_type=ProcessorType.CANDIDATE_EXTRACTION.value,
            config_version=config_version,
        )
        if existing_run and existing_run.status in (
            ProcessingStatus.COMPLETED,
            ProcessingStatus.RUNNING,
        ):
            return existing_run.id

        run_id = uuid.uuid4()
        run = ProcessingRunORM(
            id=run_id,
            evidence_id=evidence_id,
            processor_type=ProcessorType.CANDIDATE_EXTRACTION.value,
            provider=self.settings.extraction_provider,
            status=ProcessingStatus.RUNNING.value,
            config_version=config_version,
            started_at=datetime.now(UTC),
        )
        await self.processing_repo.add_run(run)

        try:
            extraction_result = await self.extraction_provider.extract_candidates(text, str(run_id))

            ext_run = ExtractionRunORM(
                id=uuid.uuid4(),
                processing_run_id=run_id,
                provider_version=extraction_result.provider_version,
            )
            self.processing_repo.session.add(ext_run)

            for candidate in extraction_result.candidates:
                # Convert provenance objects to dict
                prov_dicts = []
                for p in candidate.provenance:
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
            run.completed_at = datetime.now(UTC)

        except Exception as e:
            self.logger.error(f"Extraction Pipeline failed for run {run_id}: {e}")
            run.status = ProcessingStatus.FAILED.value
            run.failure_reason = str(e)
            run.completed_at = datetime.now(UTC)

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
