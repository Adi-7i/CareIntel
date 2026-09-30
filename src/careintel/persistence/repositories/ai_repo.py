"""
AI Repository.

Handles persistence for AI runs, drafts, and policy decisions.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.ai import AIDraftORM, AIRunORM, PolicyDecisionORM


class AIRepository:
    """Data access layer for AI executions and drafts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── AI Runs ───────────────────────────────────────────────────────────────

    async def get_run_by_idempotency_key(
        self,
        case_id: uuid.UUID,
        task_type: str,
        input_hash: str | None,
        prompt_version: str,
    ) -> AIRunORM | None:
        """Find an existing AI run to enforce idempotency."""
        stmt = select(AIRunORM).where(
            AIRunORM.case_id == case_id,
            AIRunORM.task_type == task_type,
            AIRunORM.prompt_version == prompt_version,
        )
        if input_hash is not None:
            stmt = stmt.where(AIRunORM.input_hash == input_hash)
        else:
            stmt = stmt.where(AIRunORM.input_hash.is_(None))

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_run(self, data: dict[str, Any]) -> AIRunORM:
        orm = AIRunORM(**data)
        self._session.add(orm)
        await self._session.flush()
        return orm

    async def get_run(self, run_id: uuid.UUID) -> AIRunORM | None:
        return await self._session.get(AIRunORM, run_id)

    async def update_run(self, run_id: uuid.UUID, updates: dict[str, Any]) -> None:
        await self._session.execute(update(AIRunORM).where(AIRunORM.id == run_id).values(**updates))
        await self._session.flush()

    # ── AI Drafts ─────────────────────────────────────────────────────────────

    async def create_draft(self, data: dict[str, Any]) -> AIDraftORM:
        orm = AIDraftORM(**data)
        self._session.add(orm)
        await self._session.flush()
        return orm

    async def get_draft_for_run(self, run_id: uuid.UUID) -> AIDraftORM | None:
        result = await self._session.execute(
            select(AIDraftORM).where(AIDraftORM.ai_run_id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_draft(self, draft_id: uuid.UUID) -> AIDraftORM | None:
        result = await self._session.execute(select(AIDraftORM).where(AIDraftORM.id == draft_id))
        return result.scalar_one_or_none()

    async def get_draft_for_update(
        self, draft_id: uuid.UUID, expected_version: int | None = None
    ) -> AIDraftORM | None:
        stmt = select(AIDraftORM).where(AIDraftORM.id == draft_id).with_for_update()
        if expected_version is not None:
            stmt = stmt.where(AIDraftORM.version == expected_version)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_drafts_for_case(self, case_id: uuid.UUID) -> list[AIDraftORM]:
        result = await self._session.execute(
            select(AIDraftORM)
            .join(AIRunORM, AIRunORM.id == AIDraftORM.ai_run_id)
            .where(AIRunORM.case_id == case_id)
            .order_by(AIDraftORM.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_draft_case_id(self, draft_id: uuid.UUID) -> uuid.UUID | None:
        result = await self._session.execute(
            select(AIRunORM.case_id)
            .join(AIDraftORM, AIDraftORM.ai_run_id == AIRunORM.id)
            .where(AIDraftORM.id == draft_id)
        )
        return result.scalar_one_or_none()

    async def get_policy_decisions_for_case(self, case_id: uuid.UUID) -> list[PolicyDecisionORM]:
        result = await self._session.execute(
            select(PolicyDecisionORM)
            .join(AIRunORM, AIRunORM.id == PolicyDecisionORM.ai_run_id)
            .where(AIRunORM.case_id == case_id)
            .order_by(PolicyDecisionORM.created_at)
        )
        return list(result.scalars().all())

    async def update_draft(self, draft_id: uuid.UUID, updates: dict[str, Any]) -> None:
        await self._session.execute(
            update(AIDraftORM).where(AIDraftORM.id == draft_id).values(**updates)
        )
        await self._session.flush()

    # ── Policy Decisions ──────────────────────────────────────────────────────

    async def create_policy_decisions(
        self, data_list: list[dict[str, Any]]
    ) -> list[PolicyDecisionORM]:
        if not data_list:
            return []
        orms = [PolicyDecisionORM(**d) for d in data_list]
        self._session.add_all(orms)
        await self._session.flush()
        return orms
