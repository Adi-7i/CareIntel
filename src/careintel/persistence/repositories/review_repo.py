"""
Review repositories.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.review import (
    DraftEditVersionORM,
    EscalationRecordORM,
    ReviewDecisionORM,
    ReviewerNoteORM,
    ReviewQueueItemORM,
)


class ReviewRepository:
    """Repository for review queue and related entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Queue Items ─────────────────────────────────────────────────────────

    async def get_queue_item(self, case_id: uuid.UUID) -> ReviewQueueItemORM | None:
        stmt = select(ReviewQueueItemORM).where(ReviewQueueItemORM.case_id == case_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_queue_item_for_update(
        self, case_id: uuid.UUID, expected_version: int | None = None
    ) -> ReviewQueueItemORM | None:
        """
        Get queue item with pessimistic lock.
        If expected_version is provided, uses optimistic concurrency control as well.
        """
        stmt = select(ReviewQueueItemORM).where(ReviewQueueItemORM.case_id == case_id).with_for_update()
        if expected_version is not None:
            stmt = stmt.where(ReviewQueueItemORM.version == expected_version)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_queue_item(self, item: ReviewQueueItemORM) -> ReviewQueueItemORM:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_queue_items(
        self,
        status: str | None = None,
        facility_id: uuid.UUID | None = None,
        assigned_to: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ReviewQueueItemORM]:
        """List queue items, optionally filtered."""
        # For simplicity, we aren't joining with CaseORM here for facility filtering,
        # but in a real implementation we would join to filter by CaseORM.facility_id
        stmt = select(ReviewQueueItemORM)
        if status:
            stmt = stmt.where(ReviewQueueItemORM.status == status)
        if assigned_to:
            stmt = stmt.where(ReviewQueueItemORM.assigned_reviewer_id == assigned_to)

        stmt = stmt.order_by(
            ReviewQueueItemORM.priority_bucket.desc(),
            ReviewQueueItemORM.entered_queue_at.asc()
        ).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ── Review Decisions ─────────────────────────────────────────────────────

    async def create_decision(self, decision: ReviewDecisionORM) -> ReviewDecisionORM:
        self.session.add(decision)
        await self.session.flush()
        return decision

    async def get_decisions_for_case(self, case_id: uuid.UUID) -> Sequence[ReviewDecisionORM]:
        stmt = (
            select(ReviewDecisionORM)
            .where(ReviewDecisionORM.case_id == case_id)
            .order_by(ReviewDecisionORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ── Draft Edit Versions ──────────────────────────────────────────────────

    async def create_draft_edit(self, edit: DraftEditVersionORM) -> DraftEditVersionORM:
        self.session.add(edit)
        await self.session.flush()
        return edit

    async def get_edits_for_draft(self, draft_id: uuid.UUID) -> Sequence[DraftEditVersionORM]:
        stmt = (
            select(DraftEditVersionORM)
            .where(DraftEditVersionORM.draft_id == draft_id)
            .order_by(DraftEditVersionORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ── Reviewer Notes ───────────────────────────────────────────────────────

    async def create_note(self, note: ReviewerNoteORM) -> ReviewerNoteORM:
        self.session.add(note)
        await self.session.flush()
        return note

    async def get_active_note_for_case(self, case_id: uuid.UUID) -> ReviewerNoteORM | None:
        stmt = select(ReviewerNoteORM).where(
            ReviewerNoteORM.case_id == case_id,
            ReviewerNoteORM.superseded_by.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Escalation Records ───────────────────────────────────────────────────

    async def create_escalation(self, escalation: EscalationRecordORM) -> EscalationRecordORM:
        self.session.add(escalation)
        await self.session.flush()
        return escalation

    async def get_escalation(self, escalation_id: uuid.UUID) -> EscalationRecordORM | None:
        return await self.session.get(EscalationRecordORM, escalation_id)

    async def get_escalations_for_case(self, case_id: uuid.UUID) -> Sequence[EscalationRecordORM]:
        stmt = (
            select(EscalationRecordORM)
            .where(EscalationRecordORM.case_id == case_id)
            .order_by(EscalationRecordORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
