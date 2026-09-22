"""Read-only infrastructure and synthetic Azure Blob verification."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncIterator

import redis.asyncio as redis
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from careintel.core.config import Settings, get_settings
from careintel.core.database import build_engine
from careintel.infrastructure.storage.azure_provider import AzureBlobProvider


async def _chunks(data: bytes, chunk_size: int = 1024) -> AsyncIterator[bytes]:
    for offset in range(0, len(data), chunk_size):
        yield data[offset : offset + chunk_size]


async def verify_postgres(settings: Settings) -> bool:
    """Verify connectivity, Alembic head, pgvector shape, and vector index."""
    print("\n--- PostgreSQL / Supabase ---")
    engine = build_engine(settings)
    started = time.perf_counter()
    try:
        expected_head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            current_head = (
                await connection.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one()
            vector_version = (
                await connection.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                )
            ).scalar_one_or_none()
            vector_type = (
                await connection.execute(
                    text(
                        """
                        SELECT format_type(a.atttypid, a.atttypmod)
                        FROM pg_attribute a
                        JOIN pg_class c ON c.oid = a.attrelid
                        WHERE c.relname = 'chunk_embeddings'
                          AND a.attname = 'embedding'
                          AND NOT a.attisdropped
                        """
                    )
                )
            ).scalar_one_or_none()
            vector_index = (
                await connection.execute(
                    text(
                        """
                        SELECT indexdef
                        FROM pg_indexes
                        WHERE tablename = 'chunk_embeddings'
                          AND indexname = 'ix_chunk_embeddings_hnsw'
                        """
                    )
                )
            ).scalar_one_or_none()

        checks = {
            "migration_head": current_head == expected_head,
            "pgvector_extension": vector_version is not None,
            "embedding_dimension": vector_type == "vector(1536)",
            "hnsw_cosine_index": bool(
                vector_index
                and "USING hnsw" in vector_index
                and "vector_cosine_ops" in vector_index
            ),
        }
        for name, passed in checks.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")
        print(f"latency_ms: {(time.perf_counter() - started) * 1000:.2f}")
        return all(checks.values())
    except Exception as exc:
        print(f"FAIL ({type(exc).__name__})")
        return False
    finally:
        await engine.dispose()


async def verify_redis(settings: Settings) -> bool:
    """Verify Redis PING without exposing the configured URL."""
    print("\n--- Redis ---")
    if not settings.redis_url:
        print("NOT VERIFIED (REDIS_URL is not configured)")
        return False

    client = redis.from_url(settings.redis_url.get_secret_value())
    started = time.perf_counter()
    try:
        passed = bool(await client.ping())
        print(f"ping: {'PASS' if passed else 'FAIL'}")
        print(f"latency_ms: {(time.perf_counter() - started) * 1000:.2f}")
        return passed
    except Exception as exc:
        print(f"FAIL ({type(exc).__name__})")
        return False
    finally:
        await client.aclose()


def verify_celery_broker_connectivity() -> bool:
    """Verify only broker connectivity; this is not worker-execution evidence."""
    print("\n--- Celery broker connectivity ---")
    started = time.perf_counter()
    try:
        from careintel.workers.celery_app import celery_app

        with celery_app.connection_for_write() as connection:
            connection.connect()
        print("broker_connection: PASS")
        print("worker_execution: NOT VERIFIED by this check")
        print(f"latency_ms: {(time.perf_counter() - started) * 1000:.2f}")
        return True
    except Exception as exc:
        print(f"FAIL ({type(exc).__name__})")
        return False


async def verify_blob(settings: Settings) -> bool:
    """Upload, retrieve, authorize, integrity-check, and delete synthetic content."""
    print("\n--- Azure Blob Storage ---")
    if not settings.azure_storage_connection_string:
        print("NOT VERIFIED (AZURE_STORAGE_CONNECTION_STRING is not configured)")
        return False

    provider = AzureBlobProvider(
        connection_string=settings.azure_storage_connection_string.get_secret_value(),
        container_name=settings.azure_storage_container,
    )
    key = f"careintel-release-verification/{uuid.uuid4()}/synthetic.txt"
    payload = b"CareIntel synthetic release verification payload"
    uploaded = False
    checks: dict[str, bool] = {}
    started = time.perf_counter()
    try:
        await provider.ensure_container()
        await provider.upload(key, _chunks(payload), "text/plain", len(payload))
        uploaded = True
        checks["upload"] = await provider.exists(key)

        downloaded = bytearray()
        async for chunk in provider.download(key):
            downloaded.extend(chunk)
        checks["content_integrity"] = bytes(downloaded) == payload

        sas_url = await provider.generate_sas_url(key, ttl_seconds=60)
        checks["authorized_read_url"] = "?" in sas_url and "sig=" in sas_url
        checks["missing_object"] = not await provider.exists(f"{key}.missing")
    except Exception as exc:
        print(f"FAIL ({type(exc).__name__})")
        return False
    finally:
        if uploaded:
            try:
                await provider.delete(key)
                checks["cleanup"] = not await provider.exists(key)
            except Exception as exc:
                print(f"cleanup: FAIL ({type(exc).__name__})")
                checks["cleanup"] = False
        await provider.close()

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"latency_ms: {(time.perf_counter() - started) * 1000:.2f}")
    return bool(checks) and all(checks.values())


async def main() -> None:
    settings = get_settings()
    results = {
        "PostgreSQL / pgvector": await verify_postgres(settings),
        "Redis": await verify_redis(settings),
        "Celery broker connectivity": verify_celery_broker_connectivity(),
        "Azure Blob": await verify_blob(settings),
    }

    print("\n--- Infrastructure summary ---")
    for name, passed in results.items():
        print(f"{name}: {'PASS' if passed else 'FAIL / NOT VERIFIED'}")
    raise SystemExit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    asyncio.run(main())
