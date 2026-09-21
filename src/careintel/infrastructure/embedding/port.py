"""
Embedding provider port (interface).

Follows the same Protocol pattern used in OCR, STT, and extraction ports.

Design invariants:
- Provider-neutral: application and domain layers never import concrete adapters.
- Dimension is declared by the provider and must match the registered EmbeddingVersion.
- Incompatible dimensions must never be mixed during retrieval.
- Demo provider returns deterministic vectors for testing without real API calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmbeddingResult:
    """
    Standardized output from an embedding provider.

    Contains the embedding vector and the provider/model metadata needed
    to register or validate against an EmbeddingVersion record.
    """

    vector: list[float]
    provider: str
    model: str
    dimension: int
    version_key: str  # Must match embedding_versions.version_key


class EmbeddingProvider(Protocol):
    """
    Protocol for embedding adapters.

    Implementations:
    - DemoEmbeddingProvider (deterministic, for testing)
    - Future: OpenAIEmbeddingProvider (production)

    Callers MUST validate that the returned dimension matches
    the registered EmbeddingVersion before persisting.
    """

    @property
    def version_key(self) -> str:
        """Unique identifier for this provider+model combination."""
        ...

    @property
    def dimension(self) -> int:
        """Declared output dimension. Must match EmbeddingVersion."""
        ...

    async def embed(self, text: str) -> EmbeddingResult:
        """
        Compute a vector embedding for the given text.

        Args:
            text: The text to embed. Treated as data, never as instructions.

        Returns:
            EmbeddingResult with vector and provenance metadata.

        Raises:
            EmbeddingProviderError: If the provider is unavailable or fails.
        """
        ...

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """
        Compute embeddings for multiple texts in a single provider call.

        Results are returned in the same order as the input texts.
        """
        ...
