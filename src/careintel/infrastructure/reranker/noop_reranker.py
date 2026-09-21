"""
No-Op Reranker — passthrough default.

Returns candidates in the same order as input.
Used when no external reranker is configured.
"""

from __future__ import annotations

from careintel.application.retrieval.fusion import FusedCandidate
from careintel.infrastructure.reranker.port import RerankProvider


class NoOpReranker:
    """Passthrough reranker: preserves the fusion-determined ordering."""

    async def rerank(
        self,
        query_text: str,
        candidates: list[FusedCandidate],
    ) -> list[FusedCandidate]:
        """Return candidates unchanged."""
        return candidates


# Verify Protocol compliance at import time
def _check_protocol() -> None:
    _: RerankProvider = NoOpReranker()


_check_protocol()
