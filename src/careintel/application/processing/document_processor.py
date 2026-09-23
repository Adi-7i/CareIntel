import logging
import os
import tempfile
import uuid
from datetime import UTC, datetime

from ulid import ULID

from careintel.application.processing.access import ProcessingAccessGuard
from careintel.core.config import Settings
from careintel.core.errors import CareIntelError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.evidence.modality import EvidenceModality
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.processing.processor_type import ProcessorType
from careintel.infrastructure.ocr.port import OcrProvider
from careintel.infrastructure.storage.port import BlobStoragePort
from careintel.persistence.models.evidence import EvidenceOutboxORM
from careintel.persistence.models.processing import (
    OcrPageORM,
    OcrRegionORM,
    OcrTableCandidateORM,
    ProcessingRunORM,
)
from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository


class DocumentProcessor:
    """Orchestrates the Document / OCR pipeline."""

    def __init__(
        self,
        settings: Settings,
        access_guard: ProcessingAccessGuard,
        processing_repo: ProcessingRepository,
        outbox_repo: EvidenceOutboxRepository,
        blob_storage: BlobStoragePort,
        ocr_provider: OcrProvider,
    ) -> None:
        self.settings = settings
        self.access_guard = access_guard
        self.processing_repo = processing_repo
        self.outbox_repo = outbox_repo
        self.blob_storage = blob_storage
        self.ocr_provider = ocr_provider
        self.logger = logging.getLogger(__name__)

    async def process(
        self, evidence_id: uuid.UUID, user: UserContext, correlation_id: str
    ) -> uuid.UUID:
        """
        Executes the Document OCR pipeline for a given evidence ID.
        Returns the ProcessingRun ID.
        """
        evidence = await self.access_guard.require_ready_evidence(evidence_id, user)

        if evidence.modality not in (EvidenceModality.DOCUMENT, EvidenceModality.IMAGE):
            raise CareIntelError(f"DocumentProcessor cannot handle modality: {evidence.modality}")

        # 4. Idempotency Check
        config_version = "v1"  # Can be updated when pipelines change
        existing_run = await self.processing_repo.get_run_by_idempotency_key(
            evidence_id=evidence_id,
            processor_type=ProcessorType.DOCUMENT_OCR.value,
            config_version=config_version,
        )
        if existing_run:
            return existing_run.id

        # 5. Create Run Record
        run_id = uuid.uuid4()
        run = ProcessingRunORM(
            id=run_id,
            evidence_id=evidence_id,
            processor_type=ProcessorType.DOCUMENT_OCR.value,
            provider=self.settings.ocr_provider,
            status=ProcessingStatus.PENDING.value,
            config_version=config_version,
            started_at=datetime.now(UTC).replace(tzinfo=None),
        )
        await self.processing_repo.add_run(run)
        run.status = ProcessingStatus.RUNNING.value

        # 6. Execute OCR in Temp Workspace
        temp_dir = self.settings.ocr_temp_workspace
        os.makedirs(temp_dir, exist_ok=True)
        suffix = os.path.splitext(evidence.original_filename or "evidence.bin")[1]
        fd, local_file_path = tempfile.mkstemp(prefix=f"ocr_{run_id}_", suffix=suffix, dir=temp_dir)

        try:
            # Download blob
            if not evidence.storage_key:
                raise CareIntelError("Evidence missing storage_key")

            with os.fdopen(fd, "wb") as f:
                async for chunk in self.blob_storage.download(evidence.storage_key):
                    f.write(chunk)

            # OCR processing
            ocr_result = await self.ocr_provider.process_document(local_file_path, str(run_id))

            # Persist output
            for page in ocr_result.pages:
                page_orm = OcrPageORM(
                    id=page.page_id,
                    run_id=run_id,
                    page_number=page.page_number,
                    width=page.width,
                    height=page.height,
                    unit=page.unit,
                    confidence=page.confidence,
                    status=page.status,
                )
                await self.processing_repo.add_ocr_page(page_orm)

                regions_for_page = [r for r in ocr_result.regions if r.page_id == page.page_id]
                region_orms = [
                    OcrRegionORM(
                        id=r.region_id,
                        page_id=page.page_id,
                        text_content=r.text,
                        reading_order=r.reading_order,
                        bounding_box=r.bounding_box,
                        confidence=r.confidence,
                    )
                    for r in regions_for_page
                ]
                await self.processing_repo.add_ocr_regions(region_orms)

                tables_for_page = [
                    table for table in ocr_result.tables if table.page_number == page.page_number
                ]
                await self.processing_repo.add_ocr_tables(
                    [
                        OcrTableCandidateORM(
                            id=uuid.uuid4(),
                            page_id=page.page_id,
                            cells_json={
                                "row_count": table.row_count,
                                "column_count": table.column_count,
                                "cells": table.cells,
                                "markdown": table.markdown,
                            },
                            confidence=None,
                        )
                        for table in tables_for_page
                    ]
                )

            run.status = ProcessingStatus.COMPLETED.value
            run.completed_at = datetime.now(UTC).replace(tzinfo=None)

        except Exception as exc:
            self.logger.error(
                "OCR processing failed",
                extra={"run_id": str(run_id), "error_type": type(exc).__name__},
            )
            run.status = ProcessingStatus.FAILED.value
            run.failure_reason = type(exc).__name__
            run.completed_at = datetime.now(UTC).replace(tzinfo=None)

        finally:
            if os.path.exists(local_file_path):
                os.remove(local_file_path)

        # 7. Emit Outbox Event using Existing Infrastructure
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
                "processor_type": ProcessorType.DOCUMENT_OCR.value,
                "status": run.status,
            },
        )
        await self.outbox_repo.append(outbox_event)

        return run_id
