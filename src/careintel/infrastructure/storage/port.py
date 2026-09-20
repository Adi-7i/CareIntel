"""
Blob storage interface.
"""

from collections.abc import AsyncIterator
from typing import Protocol


class BlobStoragePort(Protocol):
    """
    Interface for interacting with blob storage (e.g. Azure Blob).
    """

    async def upload(
        self, key: str, data: AsyncIterator[bytes], content_type: str, size: int
    ) -> None:
        """Upload a stream to storage."""
        ...

    def download(self, key: str) -> AsyncIterator[bytes]:
        """Download a stream from storage."""
        ...

    async def delete(self, key: str) -> None:
        """Delete an object from storage."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if an object exists in storage."""
        ...

    async def generate_sas_url(self, key: str, ttl_seconds: int) -> str:
        """Generate a secure, short-lived download URL."""
        ...
