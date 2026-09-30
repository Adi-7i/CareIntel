"""
Structuring persistence layer.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.structuring import (
    ClarificationQuestionORM,
    ConflictCandidateLinkORM,
    ConflictRecordORM,
    MissingInfoItemORM,
    StructuringRunORM,
    TimelineEventORM,
)


class StructuringRepository:
    """Repository for Phase 6 Structuring Engine entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_run_by_idempotency_key(
        self, case_id: uuid.UUID, extraction_run_id: uuid.UUID
    ) -> StructuringRunORM | None:
        """Find an existing structuring run by its idempotency key."""
        stmt = select(StructuringRunORM).where(
            StructuringRunORM.case_id == case_id,
            StructuringRunORM.extraction_run_id == extraction_run_id,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def create_run(self, run: StructuringRunORM) -> None:
        """Create a new structuring run."""
        self._session.add(run)
        await self._session.flush()

    async def get_run(self, run_id: uuid.UUID) -> StructuringRunORM | None:
        return await self._session.get(StructuringRunORM, run_id)

    async def update_run_status(self, run_id: uuid.UUID, status: str, **kwargs: Any) -> None:
        """Update a run's status and arbitrary kwargs."""
        stmt = (
            update(StructuringRunORM)
            .where(StructuringRunORM.id == run_id)
            .values(status=status, **kwargs)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def save_timeline_events(self, events: list[TimelineEventORM]) -> None:
        if not events:
            return
        self._session.add_all(events)
        await self._session.flush()

    async def save_conflict_records(
        self, conflicts: list[ConflictRecordORM], links: list[ConflictCandidateLinkORM]
    ) -> None:
        if conflicts:
            self._session.add_all(conflicts)
        if links:
            self._session.add_all(links)
        await self._session.flush()

    async def save_missing_info_items(self, items: list[MissingInfoItemORM]) -> None:
        if not items:
            return
        self._session.add_all(items)
        await self._session.flush()

    async def save_questions(self, questions: list[ClarificationQuestionORM]) -> None:
        if not questions:
            return
        self._session.add_all(questions)
        await self._session.flush()

    async def get_latest_successful_run(self, case_id: uuid.UUID) -> StructuringRunORM | None:
        stmt = (
            select(StructuringRunORM)
            .where(
                StructuringRunORM.case_id == case_id,
                StructuringRunORM.status.in_(["COMPLETED", "NO_INPUT"]),
            )
            .order_by(StructuringRunORM.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_timeline_events(
        self, case_id: uuid.UUID, run_id: uuid.UUID
    ) -> list[TimelineEventORM]:
        stmt = select(TimelineEventORM).where(
            TimelineEventORM.case_id == case_id,
            TimelineEventORM.structuring_run_id == run_id,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_conflict_records(
        self, case_id: uuid.UUID, run_id: uuid.UUID
    ) -> list[ConflictRecordORM]:
        stmt = select(ConflictRecordORM).where(
            ConflictRecordORM.case_id == case_id,
            ConflictRecordORM.detection_run_id == run_id,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_missing_info_items(
        self, case_id: uuid.UUID, run_id: uuid.UUID
    ) -> list[MissingInfoItemORM]:
        stmt = select(MissingInfoItemORM).where(
            MissingInfoItemORM.case_id == case_id,
            MissingInfoItemORM.evaluation_run_id == run_id,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_clarification_questions(
        self, case_id: uuid.UUID, run_id: uuid.UUID | None = None
    ) -> list[ClarificationQuestionORM]:
        stmt = select(ClarificationQuestionORM).where(ClarificationQuestionORM.case_id == case_id)
        if run_id is not None:
            stmt = stmt.where(ClarificationQuestionORM.evaluation_run_id == run_id)
        stmt = stmt.order_by(ClarificationQuestionORM.created_at, ClarificationQuestionORM.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
