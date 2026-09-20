"""
Tests for FakeBlobProvider.
"""

from collections.abc import AsyncIterator

import pytest

from careintel.core.errors import StorageError
from careintel.infrastructure.storage.fake_provider import FakeBlobProvider


@pytest.mark.asyncio
async def test_fake_blob_provider_lifecycle() -> None:
    provider = FakeBlobProvider()

    # Exists check
    assert await provider.exists("test-key") is False

    # Upload
    async def stream_data() -> AsyncIterator[bytes]:
        yield b"hello "
        yield b"world"

    await provider.upload("test-key", stream_data(), "text/plain", 11)

    assert await provider.exists("test-key") is True

    # Overwrite fails
    with pytest.raises(StorageError):
        await provider.upload("test-key", stream_data(), "text/plain", 11)

    # Download
    chunks = []
    async for chunk in provider.download("test-key"):
        chunks.append(chunk)
    assert b"".join(chunks) == b"hello world"

    # SAS URL
    url = await provider.generate_sas_url("test-key", 3600)
    assert "fake-sas-token" in url

    # Delete
    await provider.delete("test-key")
    assert await provider.exists("test-key") is False

    # Download missing
    with pytest.raises(StorageError):
        async for _ in provider.download("test-key"):
            pass
