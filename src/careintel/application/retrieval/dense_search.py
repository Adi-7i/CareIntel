"""
Dense vector search using pgvector cosine similarity.

Queries the `chunk_embeddings` table using pgvector's cosine distance
operator (<=>). Returns scored candidates in descending similarity order.

DESIGN:
- Scoped to a specific embedding_version_id to prevent dimension mixing.
- Returns raw (source_id, dense_score) pairs; the retrieval service
  assembles them into RetrievalCandidate objects.
- No thresholds are applied — all results are returned and fusion decides.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class DenseSearchResult:
    """A single dense retrieval result before fusion."""

    chunk_id: uuid.UUID
    dense_score: float  # Cosine similarity (0-1, higher = more similar)


class DenseSearcher:
    """
    Performs pgvector cosine similarity search over knowledge chunk embeddings.

    The embedding column must be populated before search is possible.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        query_vector: list[float],
        embedding_version_id: uuid.UUID,
        top_k: int,
        publication_status: str = "PUBLISHED",
    ) -> list[DenseSearchResult]:
        """
        Find the top-k knowledge chunks most similar to the query vector.

        Args:
            query_vector:         Embedding for the query text.
            embedding_version_id: Must match the stored chunk embeddings.
            top_k:                Maximum number of results to return.
            publication_status:   Filter to chunks from published sources.

        Returns:
            List of DenseSearchResult ordered by descending similarity.
            Empty list if no chunks are available.
        """
        if not query_vector:
            return []

        vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

        # pgvector cosine distance: 1 - (a <=> b) = cosine similarity
        # We use (1 - distance) to return similarity scores (higher = better)
        result = await self._session.execute(
            text(
                """
                SELECT
                    ce.chunk_id,
                    (1.0 - (ce.embedding <=> :query_vec::vector)) AS dense_score
                FROM chunk_embeddings ce
                JOIN knowledge_chunks kc ON kc.id = ce.chunk_id
                JOIN knowledge_versions kv ON kv.id = kc.version_id
                JOIN knowledge_sources ks ON ks.id = kv.source_id
                WHERE
                    ce.embedding_version_id = :emb_version_id
                    AND kc.status = 'ACTIVE'
                    AND ks.publication_status = :pub_status
                ORDER BY ce.embedding <=> :query_vec::vector
                LIMIT :top_k
                """
            ),
            {
                "query_vec": vector_str,
                "emb_version_id": embedding_version_id,
                "pub_status": publication_status,
                "top_k": top_k,
            },
        )

        rows = result.fetchall()
        return [
            DenseSearchResult(chunk_id=row[0], dense_score=float(row[1]))
            for row in rows
        ]
