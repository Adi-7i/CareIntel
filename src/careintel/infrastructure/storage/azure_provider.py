"""
Azure Blob Storage provider.
"""

import datetime
from collections.abc import AsyncIterator

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient

from careintel.core.errors import StorageError
from careintel.infrastructure.storage.port import BlobStoragePort


class AzureBlobProvider(BlobStoragePort):
    """
    Azure Blob Storage implementation.
    """

    def __init__(self, connection_string: str, container_name: str) -> None:
        self._client = BlobServiceClient.from_connection_string(connection_string)
        self._container_name = container_name
        self._container_client = self._client.get_container_client(container_name)
        # Assumes container is private

    async def upload(
        self, key: str, data: AsyncIterator[bytes], content_type: str, size: int
    ) -> None:
        try:
            blob_client = self._container_client.get_blob_client(key)
            # The length parameter is not strictly required but helpful if known
            await blob_client.upload_blob(data, length=size, overwrite=False)
        except Exception as e:
            raise StorageError(f"Failed to upload to Azure Blob Storage: {e}") from e

    async def download(self, key: str) -> AsyncIterator[bytes]:
        try:
            blob_client = self._container_client.get_blob_client(key)
            stream = await blob_client.download_blob()
            async for chunk in stream.chunks():
                yield chunk
        except Exception as e:
            raise StorageError(f"Failed to download from Azure Blob Storage: {e}") from e

    async def delete(self, key: str) -> None:
        try:
            blob_client = self._container_client.get_blob_client(key)
            await blob_client.delete_blob()
        except ResourceNotFoundError:
            pass
        except Exception as e:
            raise StorageError(f"Azure Blob Storage delete failed: {e}") from e

    async def exists(self, key: str) -> bool:
        try:
            blob_client = self._container_client.get_blob_client(key)
            return await blob_client.exists()
        except Exception as e:
            raise StorageError(f"Failed to check existence in Azure Blob Storage: {e}") from e

    async def generate_sas_url(self, key: str, ttl_seconds: int) -> str:
        try:
            blob_client = self._container_client.get_blob_client(key)
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name or "",
                container_name=self._container_name,
                blob_name=key,
                account_key=blob_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(seconds=ttl_seconds),
            )
            return f"{blob_client.url}?{sas_token}"
        except Exception as e:
            raise StorageError(f"Failed to generate SAS URL: {e}") from e
