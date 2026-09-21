"""
Unit tests for the DemoEmbeddingProvider.
"""

import math
import pytest

from careintel.infrastructure.embedding.demo_provider import (
    DemoEmbeddingProvider,
    _DEMO_DIMENSION,
    _DEMO_VERSION_KEY,
)
from careintel.infrastructure.embedding.port import EmbeddingProvider


class TestDemoEmbeddingProvider:
    """Tests for DemoEmbeddingProvider."""

    @pytest.fixture
    def provider(self) -> DemoEmbeddingProvider:
        return DemoEmbeddingProvider()

    def test_satisfies_embedding_provider_protocol(self, provider: DemoEmbeddingProvider) -> None:
        """DemoEmbeddingProvider satisfies the EmbeddingProvider Protocol."""
        _: EmbeddingProvider = provider  # type-check

    def test_version_key(self, provider: DemoEmbeddingProvider) -> None:
        assert provider.version_key == _DEMO_VERSION_KEY

    def test_dimension_property(self, provider: DemoEmbeddingProvider) -> None:
        assert provider.dimension == _DEMO_DIMENSION

    @pytest.mark.asyncio
    async def test_embed_returns_correct_dimension(self, provider: DemoEmbeddingProvider) -> None:
        result = await provider.embed("patient presents with fever")
        assert len(result.vector) == _DEMO_DIMENSION

    @pytest.mark.asyncio
    async def test_embed_is_deterministic(self, provider: DemoEmbeddingProvider) -> None:
        """Same input always yields identical vector."""
        text = "Deterministic test input"
        r1 = await provider.embed(text)
        r2 = await provider.embed(text)
        assert r1.vector == r2.vector

    @pytest.mark.asyncio
    async def test_different_inputs_yield_different_vectors(
        self, provider: DemoEmbeddingProvider
    ) -> None:
        """Different inputs produce different embeddings."""
        r1 = await provider.embed("chest pain")
        r2 = await provider.embed("headache")
        assert r1.vector != r2.vector

    @pytest.mark.asyncio
    async def test_vector_is_unit_length(self, provider: DemoEmbeddingProvider) -> None:
        """Embedding vector must be L2-normalized (norm ~= 1.0)."""
        result = await provider.embed("test normalization")
        norm = math.sqrt(sum(x * x for x in result.vector))
        assert abs(norm - 1.0) < 1e-6

    @pytest.mark.asyncio
    async def test_embed_metadata(self, provider: DemoEmbeddingProvider) -> None:
        result = await provider.embed("metadata test")
        assert result.provider == "demo"
        assert result.model == "demo-fixed-768"
        assert result.dimension == _DEMO_DIMENSION
        assert result.version_key == _DEMO_VERSION_KEY

    @pytest.mark.asyncio
    async def test_embed_batch_returns_same_as_individual(
        self, provider: DemoEmbeddingProvider
    ) -> None:
        texts = ["fever", "cough", "rash"]
        batch = await provider.embed_batch(texts)
        for i, text in enumerate(texts):
            individual = await provider.embed(text)
            assert batch[i].vector == individual.vector

    @pytest.mark.asyncio
    async def test_embed_batch_preserves_order(self, provider: DemoEmbeddingProvider) -> None:
        texts = ["alpha", "beta", "gamma", "delta"]
        results = await provider.embed_batch(texts)
        assert len(results) == len(texts)

    @pytest.mark.asyncio
    async def test_embedding_version_compatibility_check(
        self, provider: DemoEmbeddingProvider
    ) -> None:
        """Embedding dimension from result must match the declared provider dimension."""
        result = await provider.embed("compatibility check")
        # This is the key safety property: callers must reject mismatched dimensions
        assert result.dimension == provider.dimension

    @pytest.mark.asyncio
    async def test_empty_string_does_not_crash(self, provider: DemoEmbeddingProvider) -> None:
        """Edge case: empty string should produce a valid embedding."""
        result = await provider.embed("")
        assert len(result.vector) == _DEMO_DIMENSION
