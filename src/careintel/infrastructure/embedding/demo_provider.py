"""
Deterministic Demo Embedding Provider.

Returns stable, deterministic vectors for development and testing.

IMPORTANT:
- This provider does NOT call any external API.
- Demo embeddings are NOT semantically meaningful.
- They are NOT suitable for production retrieval.
- They are designed to be deterministic so tests are reproducible.
- Real provider integration must be explicitly configured and validated
  with actual credentials before any production use.

The demo vector is computed from a hash of the input text, ensuring:
- Same input → same output (deterministic)
- Different inputs → different outputs (not all-zeros)
- Correct dimension (768 by default)
- Values in a plausible float range (-1.0 to 1.0)
"""

from __future__ import annotations

import hashlib
import math
import struct

from careintel.infrastructure.embedding.port import EmbeddingProvider, EmbeddingResult

# Demo configuration constants
_DEMO_PROVIDER = "demo"
_DEMO_MODEL = "demo-fixed-768"
_DEMO_DIMENSION = 768
_DEMO_VERSION_KEY = "demo-fixed-768-v1"


class DemoEmbeddingProvider:
    """
    Deterministic embedding provider for development and testing.

    Produces a stable vector derived from a SHA-256 hash of the input text.
    The vector is normalized to unit length (L2 norm = 1.0) so cosine
    similarity comparisons are meaningful in tests.
    """

    @property
    def version_key(self) -> str:
        return _DEMO_VERSION_KEY

    @property
    def dimension(self) -> int:
        return _DEMO_DIMENSION

    async def embed(self, text: str) -> EmbeddingResult:
        """
        Compute a deterministic embedding for the given text.

        The implementation uses repeated SHA-256 hashing to generate
        768 float32 values, then normalizes to unit length.
        """
        vector = self._deterministic_vector(text)
        return EmbeddingResult(
            vector=vector,
            provider=_DEMO_PROVIDER,
            model=_DEMO_MODEL,
            dimension=_DEMO_DIMENSION,
            version_key=_DEMO_VERSION_KEY,
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Compute embeddings for a batch of texts."""
        return [await self.embed(text) for text in texts]

    @staticmethod
    def _deterministic_vector(text: str) -> list[float]:
        """
        Produce a deterministic, normalized float vector from text.

        Uses SHA-256 chained hashing to fill the required dimensions.
        The result is L2-normalized for cosine similarity compatibility.
        """
        dim = _DEMO_DIMENSION
        raw: list[float] = []

        # Seed from text hash; chain hashes until we have enough bytes
        seed = text.encode("utf-8")
        while len(raw) < dim:
            digest = hashlib.sha256(seed).digest()
            # Unpack up to 8 float32 values per 32-byte digest
            n_floats = min(8, dim - len(raw))
            for i in range(n_floats):
                # Extract 4 bytes → interpret as signed int16 pair → float
                chunk = digest[i * 4 : i * 4 + 4]
                (val,) = struct.unpack(">i", chunk)
                raw.append(float(val))
            seed = digest  # Chain: next iteration hashes the previous digest

        raw = raw[:dim]

        # L2-normalize
        norm = math.sqrt(sum(x * x for x in raw))
        if norm == 0.0:
            # Degenerate case: return zero vector (shouldn't happen in practice)
            return [0.0] * dim
        return [x / norm for x in raw]


# Verify Protocol compliance at import time (type-checker aid)
def _check_protocol() -> None:
    _: EmbeddingProvider = DemoEmbeddingProvider()


_check_protocol()
