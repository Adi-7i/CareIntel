"""
Retrieval Repository.

Handles persistence for retrieval_runs and retrieval_candidates.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.retrieval import RetrievalCandidateORM, RetrievalRunORM


class RetrievalRepository:
    """Data access layer for retrieval audits and results."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_run_by_idempotency_key(
        self,
        case_id: uuid.UUID | None,
        query_hash: str,
        corpus_version: str | None,
        search_mode: str,
    ) -> RetrievalRunORM | None:
        """
        Find an existing retrieval run to enforce idempotency.
        """
        stmt = select(RetrievalRunORM).where(
            RetrievalRunORM.query_hash == query_hash,
            RetrievalRunORM.search_mode == search_mode,
        )
        if case_id is not None:
            stmt = stmt.where(RetrievalRunORM.case_id == case_id)
        else:
            stmt = stmt.where(RetrievalRunORM.case_id.is_(None))

        if corpus_version is not None:
            stmt = stmt.where(RetrievalRunORM.corpus_version == corpus_version)
        else:
            stmt = stmt.where(RetrievalRunORM.corpus_version.is_(None))

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_run(self, run_id: uuid.UUID) -> RetrievalRunORM | None:
        result = await self._session.execute(
            select(RetrievalRunORM).where(RetrievalRunORM.id == run_id)
        )
        return result.scalar_one_or_none()

    async def create_run(self, data: dict[str, Any]) -> RetrievalRunORM:
        orm = RetrievalRunORM(**data)
        self._session.add(orm)
        await self._session.flush()
        return orm

    async def create_candidates(
        self, data_list: list[dict[str, Any]]
    ) -> list[RetrievalCandidateORM]:
        if not data_list:
            return []
        orms = [RetrievalCandidateORM(**d) for d in data_list]
        self._session.add_all(orms)
        await self._session.flush()
        return orms

    async def get_candidates_for_run(self, run_id: uuid.UUID) -> list[RetrievalCandidateORM]:
        result = await self._session.execute(
            select(RetrievalCandidateORM)
            .where(RetrievalCandidateORM.retrieval_run_id == run_id)
            .order_by(RetrievalCandidateORM.rank)
        )
        return list(result.scalars().all())
