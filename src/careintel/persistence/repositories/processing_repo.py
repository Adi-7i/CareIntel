"""
Processing Repository.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.processing import (
    OcrPageORM,
    OcrRegionORM,
    ProcessingRunORM,
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

    async def get_ocr_pages_for_run(self, run_id: uuid.UUID) -> Sequence[OcrPageORM]:
        stmt = select(OcrPageORM).where(OcrPageORM.run_id == run_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_ocr_regions_for_page(self, page_id: uuid.UUID) -> Sequence[OcrRegionORM]:
        stmt = select(OcrRegionORM).where(OcrRegionORM.page_id == page_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
