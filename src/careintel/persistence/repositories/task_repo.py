"""
Async Task Repository.
"""

import datetime
import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.domain.workflow.task_states import AsyncTaskStatus
from careintel.persistence.models.workflow import AsyncTaskORM


class AsyncTaskRepository:
    """Repository for managing async tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, task_id: uuid.UUID) -> AsyncTaskORM | None:
        """Get a task by ID."""
        return await self.session.get(AsyncTaskORM, task_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> AsyncTaskORM | None:
        """Find an existing task by its idempotency key."""
        stmt = select(AsyncTaskORM).where(AsyncTaskORM.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_case(self, case_id: uuid.UUID) -> Sequence[AsyncTaskORM]:
        """List tasks associated with a case."""
        stmt = select(AsyncTaskORM).where(AsyncTaskORM.case_id == case_id).order_by(AsyncTaskORM.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def append(self, task: AsyncTaskORM) -> AsyncTaskORM:
        """Save a new task."""
        self.session.add(task)
        await self.session.flush()
        return task

    async def update_status(self, task_id: uuid.UUID, status: AsyncTaskStatus) -> None:
        """Update the status of a task."""
        now = datetime.datetime.now(datetime.UTC)
        updates = {"status": status.value}

        if status == AsyncTaskStatus.QUEUED:
            updates["queued_at"] = now
        elif status == AsyncTaskStatus.RUNNING:
            # First time transition to running sets started_at
            # Subsequent (retry) just updates heartbeat
            updates["heartbeat_at"] = now
        elif status in (AsyncTaskStatus.SUCCEEDED, AsyncTaskStatus.FAILED, AsyncTaskStatus.CANCELLED):
            updates["completed_at"] = now

        stmt = update(AsyncTaskORM).where(AsyncTaskORM.id == task_id).values(**updates)
        await self.session.execute(stmt)
        await self.session.flush()

    async def update_heartbeat(self, task_id: uuid.UUID) -> None:
        """Update the heartbeat timestamp for a running task."""
        stmt = (
            update(AsyncTaskORM)
            .where(AsyncTaskORM.id == task_id, AsyncTaskORM.status == AsyncTaskStatus.RUNNING.value)
            .values(heartbeat_at=datetime.datetime.now(datetime.UTC))
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def find_stale_tasks(self, stale_threshold: datetime.datetime) -> Sequence[AsyncTaskORM]:
        """Find tasks that have been RUNNING but haven't updated heartbeat since threshold."""
        stmt = select(AsyncTaskORM).where(
            AsyncTaskORM.status == AsyncTaskStatus.RUNNING.value,
            (AsyncTaskORM.heartbeat_at < stale_threshold) | (AsyncTaskORM.heartbeat_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
