"""
Processing Repository.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.processing import (
    ExtractedCandidateORM,
    ExtractionRunORM,
    LanguageResultORM,
    OcrPageORM,
    OcrRegionORM,
    OcrTableCandidateORM,
    ProcessingRunORM,
    TranscriptRunORM,
    TranscriptSegmentORM,
)


class ProcessingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run_by_id(self, run_id: uuid.UUID) -> ProcessingRunORM | None:
        return await self.session.get(ProcessingRunORM, run_id)

    async def get_run_by_idempotency_key(
        self, evidence_id: uuid.UUID, processor_type: str, config_version: str
    ) -> ProcessingRunORM | None:
        stmt = select(ProcessingRunORM).where(
            ProcessingRunORM.evidence_id == evidence_id,
            ProcessingRunORM.processor_type == processor_type,
            ProcessingRunORM.config_version == config_version,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_runs_for_evidence(self, evidence_id: uuid.UUID) -> Sequence[ProcessingRunORM]:
        stmt = select(ProcessingRunORM).where(ProcessingRunORM.evidence_id == evidence_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_completed_runs_for_evidence(
        self, evidence_id: uuid.UUID
    ) -> Sequence[ProcessingRunORM]:
        stmt = (
            select(ProcessingRunORM)
            .where(
                ProcessingRunORM.evidence_id == evidence_id,
                ProcessingRunORM.status == "COMPLETED",
            )
            .order_by(ProcessingRunORM.created_at, ProcessingRunORM.id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_run(self, run: ProcessingRunORM) -> ProcessingRunORM:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_ocr_page(self, page: OcrPageORM) -> OcrPageORM:
        self.session.add(page)
        await self.session.flush()
        return page

    async def add_ocr_regions(self, regions: list[OcrRegionORM]) -> None:
        self.session.add_all(regions)
        await self.session.flush()

    async def add_ocr_tables(self, tables: list[OcrTableCandidateORM]) -> None:
        if not tables:
            return
        self.session.add_all(tables)
        await self.session.flush()

    async def get_ocr_pages_for_run(self, run_id: uuid.UUID) -> Sequence[OcrPageORM]:
        stmt = select(OcrPageORM).where(OcrPageORM.run_id == run_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_ocr_regions_for_page(self, page_id: uuid.UUID) -> Sequence[OcrRegionORM]:
        stmt = select(OcrRegionORM).where(OcrRegionORM.page_id == page_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_ocr_regions_for_run(self, run_id: uuid.UUID) -> list[OcrRegionORM]:
        stmt = (
            select(OcrRegionORM)
            .join(OcrPageORM, OcrPageORM.id == OcrRegionORM.page_id)
            .where(OcrPageORM.run_id == run_id)
            .order_by(OcrPageORM.page_number, OcrRegionORM.reading_order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_transcript_run(self, processing_run_id: uuid.UUID) -> TranscriptRunORM | None:
        result = await self.session.execute(
            select(TranscriptRunORM).where(TranscriptRunORM.processing_run_id == processing_run_id)
        )
        return result.scalar_one_or_none()

    async def get_transcript_segments_for_run(
        self, processing_run_id: uuid.UUID
    ) -> list[TranscriptSegmentORM]:
        stmt = (
            select(TranscriptSegmentORM)
            .join(
                TranscriptRunORM,
                TranscriptRunORM.id == TranscriptSegmentORM.transcript_run_id,
            )
            .where(TranscriptRunORM.processing_run_id == processing_run_id)
            .order_by(TranscriptSegmentORM.start_time_ms, TranscriptSegmentORM.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_language_result(self, processing_run_id: uuid.UUID) -> LanguageResultORM | None:
        result = await self.session.execute(
            select(LanguageResultORM).where(
                LanguageResultORM.processing_run_id == processing_run_id
            )
        )
        return result.scalar_one_or_none()

    async def get_extraction_run_for_processing(
        self, processing_run_id: uuid.UUID
    ) -> ExtractionRunORM | None:
        result = await self.session.execute(
            select(ExtractionRunORM).where(ExtractionRunORM.processing_run_id == processing_run_id)
        )
        return result.scalar_one_or_none()

    async def get_extraction_run(self, extraction_run_id: uuid.UUID) -> ExtractionRunORM | None:
        return await self.session.get(ExtractionRunORM, extraction_run_id)

    async def get_candidates_for_extraction(
        self, extraction_run_id: uuid.UUID
    ) -> list[ExtractedCandidateORM]:
        result = await self.session.execute(
            select(ExtractedCandidateORM)
            .where(ExtractedCandidateORM.extraction_run_id == extraction_run_id)
            .order_by(ExtractedCandidateORM.created_at, ExtractedCandidateORM.id)
        )
        return list(result.scalars().all())
