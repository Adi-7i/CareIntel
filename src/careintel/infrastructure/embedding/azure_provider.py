"""
Azure OpenAI Embedding Provider.

Production embedding adapter that integrates with Azure OpenAI.
Generates 1536-dimensional embeddings using text-embedding-3-small.
"""

from __future__ import annotations

from openai import AsyncAzureOpenAI

from careintel.infrastructure.embedding.port import EmbeddingResult


class AzureEmbeddingProvider:
    """
    Azure OpenAI implementation of the EmbeddingProvider Protocol.
    """

    def __init__(self, endpoint: str, api_key: str, deployment: str) -> None:
        self._client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-15-preview",
        )
        self._deployment = deployment
        self._dimension = 1536
        self._version_key = f"azure-openai-{deployment}-v1"

    @property
    def version_key(self) -> str:
        return self._version_key

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> EmbeddingResult:
        """
        Compute an embedding for a single string.
        """
        response = await self._client.embeddings.create(
            input=[text],
            model=self._deployment
        )
        vector = response.data[0].embedding
        return EmbeddingResult(
            vector=vector,
            provider="azure_openai",
            model=self._deployment,
            dimension=len(vector),
            version_key=self._version_key,
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """
        Compute embeddings for multiple strings in a single provider call.
        """
        if not texts:
            return []

        response = await self._client.embeddings.create(
            input=texts,
            model=self._deployment
        )

        results = []
        for i, data in enumerate(response.data):
            vector = data.embedding
            results.append(
                EmbeddingResult(
                    vector=vector,
                    provider="azure_openai",
                    model=self._deployment,
                    dimension=len(vector),
                    version_key=self._version_key,
                )
            )
        return results

# Verify Protocol compliance at import time (type-checker aid)
def _check_protocol() -> None:
    pass
