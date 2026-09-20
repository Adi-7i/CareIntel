"""
Fake blob storage provider for testing and local development.
"""

from collections.abc import AsyncIterator

from careintel.core.errors import StorageError
from careintel.infrastructure.storage.port import BlobStoragePort


class FakeBlobProvider(BlobStoragePort):
    """
    In-memory blob storage implementation.
    """

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def upload(
        self, key: str, data: AsyncIterator[bytes], content_type: str, size: int
    ) -> None:
        if key in self._store:
            raise StorageError("Blob already exists (FakeBlobProvider forbids overwrite)")
        chunks = []
        async for chunk in data:
            chunks.append(chunk)
        self._store[key] = b"".join(chunks)

    async def download(self, key: str) -> AsyncIterator[bytes]:
        if key not in self._store:
            raise StorageError("Blob not found")
        # Yield in 1KB chunks to simulate streaming
        data = self._store[key]
        chunk_size = 1024
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def generate_sas_url(self, key: str, ttl_seconds: int) -> str:
        if key not in self._store:
            raise StorageError("Blob not found")
        return f"https://fake-storage.local/{key}?sas_token=fake-sas-token&ttl={ttl_seconds}"
