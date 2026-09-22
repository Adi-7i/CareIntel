from collections.abc import AsyncIterator

import pytest

from careintel.core.errors import StorageError
from careintel.infrastructure.storage.fake_provider import FakeBlobProvider


async def dummy_stream(data: bytes, chunk_size: int = 1024) -> AsyncIterator[bytes]:
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


@pytest.mark.asyncio
async def test_fake_blob_upload_and_download():
    provider = FakeBlobProvider()
    key = "cases/123/documents/abc/original"
    content = b"fake pdf content"

    # Upload
    stream = dummy_stream(content)
    await provider.upload(key, stream, "application/pdf", len(content))

    # Exists
    assert await provider.exists(key) is True

    # Download
    download_stream = provider.download(key)
    downloaded_content = b""
    async for chunk in download_stream:
        downloaded_content += chunk

    assert downloaded_content == content


@pytest.mark.asyncio
async def test_fake_blob_upload_duplicate_raises():
    provider = FakeBlobProvider()
    key = "cases/123/documents/abc/original"
    content = b"fake pdf content"

    stream1 = dummy_stream(content)
    await provider.upload(key, stream1, "application/pdf", len(content))

    stream2 = dummy_stream(content)
    with pytest.raises(StorageError, match="Blob already exists"):
        await provider.upload(key, stream2, "application/pdf", len(content))


@pytest.mark.asyncio
async def test_fake_blob_download_missing_raises():
    provider = FakeBlobProvider()

    with pytest.raises(StorageError, match="Blob not found"):
        # The download method is not async itself, it returns an async generator
        # But we can test it by attempting to iterate
        stream = provider.download("missing/key")
        async for _ in stream:
            pass


@pytest.mark.asyncio
async def test_fake_blob_delete():
    provider = FakeBlobProvider()
    key = "cases/123/documents/abc/original"
    content = b"fake pdf content"

    stream = dummy_stream(content)
    await provider.upload(key, stream, "application/pdf", len(content))
    assert await provider.exists(key) is True

    await provider.delete(key)
    assert await provider.exists(key) is False

    # Deleting missing should not raise
    await provider.delete(key)


@pytest.mark.asyncio
async def test_fake_blob_sas_url():
    provider = FakeBlobProvider()
    key = "cases/123/documents/abc/original"

    with pytest.raises(StorageError, match="Blob not found"):
        await provider.generate_sas_url(key, 3600)

    stream = dummy_stream(b"content")
    await provider.upload(key, stream, "application/pdf", 7)

    url = await provider.generate_sas_url(key, 3600)
    assert url.startswith("https://fake-storage.local/")
    assert "sas_token=" in url
