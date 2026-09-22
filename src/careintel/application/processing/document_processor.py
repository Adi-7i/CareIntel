import logging
import os
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
from careintel.infrastructure.ocr.port import OcrProvider
from careintel.infrastructure.storage.port import BlobStoragePort
from careintel.persistence.models.evidence import EvidenceOutboxORM
from careintel.persistence.models.processing import OcrPageORM, OcrRegionORM, ProcessingRunORM
from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository


class DocumentProcessor:
    """Orchestrates the Document / OCR pipeline."""

    def __init__(
        self,
        settings: Settings,
        evidence_repo: EvidenceRepository,
        processing_repo: ProcessingRepository,
        outbox_repo: EvidenceOutboxRepository,
        blob_storage: BlobStoragePort,
        ocr_provider: OcrProvider,
    ) -> None:
        self.settings = settings
        self.evidence_repo = evidence_repo
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
        # Using ConsentPolicy pattern from Phase 2
        # (Assuming ConsentRepository would be needed, but we can assume evidence is READY)
        if evidence.state != EvidenceState.READY:
            raise CareIntelError(
                f"Evidence must be READY for processing. Current: {evidence.state}"
            )

        if evidence.modality not in (EvidenceModality.DOCUMENT, EvidenceModality.IMAGE):
            raise CareIntelError(f"DocumentProcessor cannot handle modality: {evidence.modality}")

        # 4. Idempotency Check
        config_version = "v1"  # Can be updated when pipelines change
        existing_run = await self.processing_repo.get_run_by_idempotency_key(
            evidence_id=evidence_id,
            processor_type=ProcessorType.DOCUMENT_OCR.value,
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
            processor_type=ProcessorType.DOCUMENT_OCR.value,
            provider=self.settings.ocr_provider,
            status=ProcessingStatus.RUNNING.value,
            config_version=config_version,
            started_at=datetime.now(UTC),
        )
        await self.processing_repo.add_run(run)

        # 6. Execute OCR in Temp Workspace
        temp_dir = self.settings.ocr_temp_workspace
        os.makedirs(temp_dir, exist_ok=True)
        local_file_path = os.path.join(temp_dir, f"{run_id}_{evidence.original_filename}")

        try:
            # Download blob
            if not evidence.storage_key:
                raise CareIntelError("Evidence missing storage_key")

            with open(local_file_path, "wb") as f:
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

            run.status = ProcessingStatus.COMPLETED.value
            run.completed_at = datetime.now(UTC)

        except Exception as e:
            self.logger.error(f"OCR Pipeline failed for run {run_id}: {e}")
            run.status = ProcessingStatus.FAILED.value
            run.failure_reason = str(e)
            run.completed_at = datetime.now(UTC)
            # Re-raise to let caller handle if they want to fail transaction
            # but usually we want to commit the failed run state.

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
