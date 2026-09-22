"""
Sparse full-text search using PostgreSQL tsvector/tsquery.

Queries the `knowledge_chunks.fts_vector` column using PostgreSQL
full-text search. Returns scored candidates via ts_rank_cd.

DESIGN:
- Uses PostgreSQL's native FTS — no external search engine required.
- fts_vector is a GENERATED ALWAYS column (computed from content).
- websearch_to_tsquery allows natural query syntax from API callers.
- Returns raw (chunk_id, sparse_score) pairs for fusion.
- No threshold is applied — all results are returned and fusion decides.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class SparseSearchResult:
    """A single sparse/FTS retrieval result before fusion."""

    chunk_id: uuid.UUID
    sparse_score: float  # ts_rank_cd score (higher = more relevant)


class SparseSearcher:
    """
    Performs PostgreSQL full-text search over knowledge chunk content.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        query_text: str,
        top_k: int,
        publication_status: str = "PUBLISHED",
    ) -> list[SparseSearchResult]:
        """
        Find the top-k knowledge chunks matching the query text.

        Args:
            query_text:        Natural language query.
            top_k:             Maximum number of results to return.
            publication_status: Filter to chunks from published sources.

        Returns:
            List of SparseSearchResult ordered by descending relevance.
            Empty list if no matches are found.
        """
        if not query_text.strip():
            return []

        result = await self._session.execute(
            text(
                """
                SELECT
                    kc.id AS chunk_id,
                    ts_rank_cd(kc.fts_vector, query) AS sparse_score
                FROM knowledge_chunks kc,
                     websearch_to_tsquery('english', :query_text) query
                JOIN knowledge_versions kv ON kv.id = kc.version_id
                JOIN knowledge_sources ks ON ks.id = kv.source_id
                WHERE
                    kc.fts_vector @@ query
                    AND kc.status = 'ACTIVE'
                    AND ks.publication_status = :pub_status
                ORDER BY sparse_score DESC
                LIMIT :top_k
                """
            ),
            {
                "query_text": query_text,
                "pub_status": publication_status,
                "top_k": top_k,
            },
        )

        rows = result.fetchall()
        return [
            SparseSearchResult(chunk_id=row[0], sparse_score=float(row[1]))
            for row in rows
        ]
