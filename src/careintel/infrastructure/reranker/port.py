"""
Reranker provider port (interface).

Optional post-retrieval reranking step that can improve ordering
of fused candidates using a cross-encoder or learned ranker.

The NoOpReranker (passthrough) is the default.
Real rerankers (e.g. Cohere Rerank) can be plugged in without
changing the retrieval or AI service layers.
"""

from __future__ import annotations

from typing import Protocol

from careintel.application.retrieval.fusion import FusedCandidate


class RerankProvider(Protocol):
    """Protocol for optional post-fusion reranking adapters."""

    async def rerank(
        self,
        query_text: str,
        candidates: list[FusedCandidate],
    ) -> list[FusedCandidate]:
        """
        Reorder candidates based on cross-encoder or learned scoring.

        Must preserve all FusedCandidate fields.
        May update the `rank` field based on new ordering.
        """
        ...
