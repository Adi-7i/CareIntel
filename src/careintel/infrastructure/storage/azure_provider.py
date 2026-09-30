"""
Azure Blob Storage provider.
"""

import datetime
from collections.abc import AsyncIterator

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient

from careintel.core.errors import StorageError
from careintel.core.logging import get_logger
from careintel.infrastructure.storage.port import BlobStoragePort

logger = get_logger(__name__)


class AzureBlobProvider(BlobStoragePort):
    """
    Azure Blob Storage implementation.
    """

    def __init__(self, connection_string: str, container_name: str) -> None:
        self._client = BlobServiceClient.from_connection_string(connection_string)
        self._container_name = container_name
        self._container_client = self._client.get_container_client(container_name)
        # Assumes container is private

    async def ensure_container(self) -> None:
        """Create container on startup if it does not exist."""
        try:
            await self._container_client.create_container()
            logger.info(f"Created Azure Blob container: {self._container_name}")
        except ResourceExistsError:
            logger.info(f"Azure Blob container {self._container_name} already exists.")
        except Exception as exc:
            logger.error(
                "Failed to verify/create Azure Blob container",
                extra={"error_type": type(exc).__name__},
            )
            raise StorageError("Container verification failed") from exc

    async def upload(
        self, key: str, data: AsyncIterator[bytes], content_type: str, size: int
    ) -> None:
        start_time = datetime.datetime.now()
        try:
            blob_client = self._container_client.get_blob_client(key)
            await blob_client.upload_blob(data, length=size, overwrite=False)
            latency = (datetime.datetime.now() - start_time).total_seconds()
            logger.info(
                "Uploaded blob to Azure Storage",
                extra={
                    "container": self._container_name,
                    "size_bytes": size,
                    "content_type": content_type,
                    "latency_s": round(latency, 3),
                    "success": True,
                },
            )
        except Exception as exc:
            latency = (datetime.datetime.now() - start_time).total_seconds()
            logger.error(
                "Failed to upload to Azure Blob Storage",
                extra={
                    "container": self._container_name,
                    "latency_s": round(latency, 3),
                    "success": False,
                    "error_type": type(exc).__name__,
                },
            )
            raise StorageError("Failed to upload to Azure Blob Storage") from exc

    async def download(self, key: str) -> AsyncIterator[bytes]:
        start_time = datetime.datetime.now()
        try:
            blob_client = self._container_client.get_blob_client(key)
            stream = await blob_client.download_blob()

            latency = (datetime.datetime.now() - start_time).total_seconds()
            logger.info(
                "Started download stream from Azure Storage",
                extra={
                    "container": self._container_name,
                    "latency_s": round(latency, 3),
                    "success": True,
                },
            )

            async for chunk in stream.chunks():
                yield chunk
        except Exception as exc:
            latency = (datetime.datetime.now() - start_time).total_seconds()
            logger.error(
                "Failed to download from Azure Blob Storage",
                extra={
                    "container": self._container_name,
                    "latency_s": round(latency, 3),
                    "success": False,
                    "error_type": type(exc).__name__,
                },
            )
            raise StorageError("Failed to download from Azure Blob Storage") from exc

    async def delete(self, key: str) -> None:
        try:
            blob_client = self._container_client.get_blob_client(key)
            await blob_client.delete_blob()
            logger.info(
                "Deleted blob from Azure Storage",
                extra={
                    "container": self._container_name,
                    "success": True,
                },
            )
        except ResourceNotFoundError:
            pass
        except Exception as exc:
            logger.error(
                "Azure Blob Storage delete failed",
                extra={
                    "container": self._container_name,
                    "success": False,
                    "error_type": type(exc).__name__,
                },
            )
            raise StorageError("Azure Blob Storage delete failed") from exc

    async def exists(self, key: str) -> bool:
        try:
            blob_client = self._container_client.get_blob_client(key)
            return await blob_client.exists()
        except Exception as exc:
            raise StorageError("Failed to check existence in Azure Blob Storage") from exc

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
        except Exception as exc:
            raise StorageError("Failed to generate SAS URL") from exc

    async def close(self) -> None:
        """Close the underlying Azure HTTP transport."""
        await self._client.close()
