"""
Unit tests for the RRF fusion algorithm.
"""

import uuid

import pytest

from careintel.application.retrieval.dense_search import DenseSearchResult
from careintel.application.retrieval.fusion import RRFFusion
from careintel.application.retrieval.sparse_search import SparseSearchResult


def make_chunk_id(n: int) -> uuid.UUID:
    return uuid.UUID(f"00000000-0000-0000-0000-{n:012d}")


class TestRRFFusion:
    """Tests for the Reciprocal Rank Fusion algorithm."""

    @pytest.fixture
    def fusion(self) -> RRFFusion:
        return RRFFusion(k=60)

    def test_dense_only_returns_correct_ranks(self, fusion: RRFFusion) -> None:
        ids = [make_chunk_id(i) for i in range(3)]
        dense = [DenseSearchResult(chunk_id=ids[i], dense_score=1.0 - i * 0.1) for i in range(3)]
        result = fusion.fuse(dense, [], top_k=3)
        assert len(result) == 3
        # Rank 1 should be the highest dense score (ids[0])
        assert result[0].chunk_id == ids[0]
        assert result[0].rank == 1

    def test_sparse_only_returns_correct_ranks(self, fusion: RRFFusion) -> None:
        ids = [make_chunk_id(i) for i in range(3)]
        sparse = [SparseSearchResult(chunk_id=ids[i], sparse_score=1.0 - i * 0.1) for i in range(3)]
        result = fusion.fuse([], sparse, top_k=3)
        assert len(result) == 3
        assert result[0].chunk_id == ids[0]

    def test_hybrid_combines_both_lists(self, fusion: RRFFusion) -> None:
        id_a = make_chunk_id(1)
        id_b = make_chunk_id(2)
        id_c = make_chunk_id(3)
        # id_a appears in dense only, id_b in sparse only, id_c in both
        dense = [
            DenseSearchResult(chunk_id=id_a, dense_score=0.9),
            DenseSearchResult(chunk_id=id_c, dense_score=0.8),
        ]
        sparse = [
            SparseSearchResult(chunk_id=id_b, sparse_score=0.9),
            SparseSearchResult(chunk_id=id_c, sparse_score=0.85),
        ]
        result = fusion.fuse(dense, sparse, top_k=3)
        # id_c appears in both, should get higher RRF score
        chunk_ids = [r.chunk_id for r in result]
        assert id_c in chunk_ids
        id_c_candidate = next(r for r in result if r.chunk_id == id_c)
        id_a_candidate = next(r for r in result if r.chunk_id == id_a)
        assert id_c_candidate.fusion_score > id_a_candidate.fusion_score

    def test_fusion_is_deterministic(self, fusion: RRFFusion) -> None:
        """Same inputs always produce the same ranked output."""
        ids = [make_chunk_id(i) for i in range(5)]
        dense = [DenseSearchResult(chunk_id=ids[i], dense_score=1.0 - i * 0.1) for i in range(5)]
        sparse = [
            SparseSearchResult(chunk_id=ids[4 - i], sparse_score=1.0 - i * 0.1) for i in range(5)
        ]

        r1 = fusion.fuse(dense, sparse, top_k=5)
        r2 = fusion.fuse(dense, sparse, top_k=5)
        assert [c.chunk_id for c in r1] == [c.chunk_id for c in r2]
        assert [c.fusion_score for c in r1] == [c.fusion_score for c in r2]

    def test_top_k_limits_results(self, fusion: RRFFusion) -> None:
        ids = [make_chunk_id(i) for i in range(10)]
        dense = [DenseSearchResult(chunk_id=ids[i], dense_score=1.0 - i * 0.05) for i in range(10)]
        result = fusion.fuse(dense, [], top_k=3)
        assert len(result) == 3

    def test_ranks_are_sequential_1_based(self, fusion: RRFFusion) -> None:
        ids = [make_chunk_id(i) for i in range(4)]
        dense = [DenseSearchResult(chunk_id=ids[i], dense_score=1.0 - i * 0.1) for i in range(4)]
        result = fusion.fuse(dense, [], top_k=4)
        assert [r.rank for r in result] == [1, 2, 3, 4]

    def test_score_provenance_preserved(self, fusion: RRFFusion) -> None:
        """Dense and sparse scores are preserved in the fused candidate."""
        id_a = make_chunk_id(1)
        dense = [DenseSearchResult(chunk_id=id_a, dense_score=0.95)]
        sparse = [SparseSearchResult(chunk_id=id_a, sparse_score=0.80)]
        result = fusion.fuse(dense, sparse, top_k=1)
        assert result[0].dense_score == 0.95
        assert result[0].sparse_score == 0.80
        assert result[0].dense_rank == 1
        assert result[0].sparse_rank == 1

    def test_dense_only_candidate_has_none_sparse(self, fusion: RRFFusion) -> None:
        id_a = make_chunk_id(1)
        dense = [DenseSearchResult(chunk_id=id_a, dense_score=0.9)]
        result = fusion.fuse(dense, [], top_k=1)
        assert result[0].sparse_score is None
        assert result[0].sparse_rank is None

    def test_sparse_only_candidate_has_none_dense(self, fusion: RRFFusion) -> None:
        id_a = make_chunk_id(1)
        sparse = [SparseSearchResult(chunk_id=id_a, sparse_score=0.9)]
        result = fusion.fuse([], sparse, top_k=1)
        assert result[0].dense_score is None
        assert result[0].dense_rank is None

    def test_empty_inputs_return_empty_list(self, fusion: RRFFusion) -> None:
        assert fusion.fuse([], [], top_k=10) == []

    def test_rrf_formula_correctness(self) -> None:
        """Verify RRF scores match the formula: Σ 1/(k + rank_i)."""
        k = 60
        fusion = RRFFusion(k=k)
        id_a = make_chunk_id(1)
        # Rank 1 in dense (position 0), rank 2 in sparse (position 1)
        dense = [
            DenseSearchResult(chunk_id=make_chunk_id(99), dense_score=0.99),
            DenseSearchResult(chunk_id=id_a, dense_score=0.9),
        ]
        sparse = [
            SparseSearchResult(chunk_id=make_chunk_id(88), sparse_score=0.99),
            SparseSearchResult(chunk_id=id_a, sparse_score=0.85),
        ]
        result = fusion.fuse(dense, sparse, top_k=3)
        candidate = next(r for r in result if r.chunk_id == id_a)
        expected_score = 1.0 / (k + 2) + 1.0 / (k + 2)  # rank 2 in both lists
        assert abs(candidate.fusion_score - expected_score) < 1e-10

    def test_top_k_larger_than_candidates(self, fusion: RRFFusion) -> None:
        """top_k > available results returns all available."""
        ids = [make_chunk_id(i) for i in range(3)]
        dense = [DenseSearchResult(chunk_id=ids[i], dense_score=0.9 - i * 0.1) for i in range(3)]
        result = fusion.fuse(dense, [], top_k=100)
        assert len(result) == 3
