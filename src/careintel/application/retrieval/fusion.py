"""
Reciprocal Rank Fusion (RRF) for hybrid retrieval.

Combines dense and sparse retrieval results into a single ranked list
using the standard Reciprocal Rank Fusion algorithm.

DESIGN:
- Algorithm is deterministic: same inputs always produce identical output.
- RRF constant k is configurable (injected, not hardcoded).
- Dense and sparse result lists are combined independently.
- Candidates appearing in both lists receive contributions from each.
- Final scores and individual scores are all preserved for audit.
- No threshold is applied at this layer.

Reference:
    Cormack, Clarke, Buettcher (2009).
    "Reciprocal Rank Fusion outperforms Condorcet and individual Rank
    Learning Methods". SIGIR 2009.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from careintel.application.retrieval.dense_search import DenseSearchResult
from careintel.application.retrieval.sparse_search import SparseSearchResult


@dataclass(frozen=True)
class FusedCandidate:
    """
    A single candidate after Reciprocal Rank Fusion.

    Carries the full scoring breakdown for audit and reranking.
    """

    chunk_id: uuid.UUID
    fusion_score: float  # RRF score (higher = better)
    rank: int  # 1-based rank in fused list
    dense_score: float | None  # Original cosine similarity; None if sparse-only
    sparse_score: float | None  # Original FTS score; None if dense-only
    dense_rank: int | None  # Rank in dense result list; None if absent
    sparse_rank: int | None  # Rank in sparse result list; None if absent


class RRFFusion:
    """
    Implements Reciprocal Rank Fusion for hybrid dense + sparse retrieval.

    The RRF formula:
        score(d) = Σ 1 / (k + rank_i(d))
        for each result list i where d appears.

    Args:
        k: RRF constant (default 60, standard value from literature).
           Configurable — not an approved product threshold.
    """

    def __init__(self, k: int = 60) -> None:
        self._k = k

    def fuse(
        self,
        dense_results: list[DenseSearchResult],
        sparse_results: list[SparseSearchResult],
        top_k: int,
    ) -> list[FusedCandidate]:
        """
        Combine dense and sparse retrieval results via RRF.

        Returns:
            Top-k FusedCandidate objects ordered by descending fusion score.
            Deterministic: same inputs always produce same output.
        """
        # Build lookup maps: chunk_id → (rank_1_based, score)
        dense_map: dict[uuid.UUID, tuple[int, float]] = {
            r.chunk_id: (i + 1, r.dense_score) for i, r in enumerate(dense_results)
        }
        sparse_map: dict[uuid.UUID, tuple[int, float]] = {
            r.chunk_id: (i + 1, r.sparse_score) for i, r in enumerate(sparse_results)
        }

        all_ids: set[uuid.UUID] = set(dense_map) | set(sparse_map)

        fused: list[FusedCandidate] = []
        for chunk_id in all_ids:
            rrf_score = 0.0

            dense_rank: int | None = None
            dense_score: float | None = None
            if chunk_id in dense_map:
                dense_rank, dense_score = dense_map[chunk_id]
                rrf_score += 1.0 / (self._k + dense_rank)

            sparse_rank: int | None = None
            sparse_score: float | None = None
            if chunk_id in sparse_map:
                sparse_rank, sparse_score = sparse_map[chunk_id]
                rrf_score += 1.0 / (self._k + sparse_rank)

            fused.append(
                FusedCandidate(
                    chunk_id=chunk_id,
                    fusion_score=rrf_score,
                    rank=0,  # assigned below after sorting
                    dense_score=dense_score,
                    sparse_score=sparse_score,
                    dense_rank=dense_rank,
                    sparse_rank=sparse_rank,
                )
            )

        # Sort by fusion_score DESC, then chunk_id for deterministic tiebreak
        fused.sort(key=lambda c: (-c.fusion_score, str(c.chunk_id)))

        # Assign 1-based ranks and slice to top_k
        return [
            FusedCandidate(
                chunk_id=c.chunk_id,
                fusion_score=c.fusion_score,
                rank=i + 1,
                dense_score=c.dense_score,
                sparse_score=c.sparse_score,
                dense_rank=c.dense_rank,
                sparse_rank=c.sparse_rank,
            )
            for i, c in enumerate(fused[:top_k])
        ]
