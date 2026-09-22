"""
Verification script for Production Infrastructure.
Verifies PostgreSQL, Redis, Azure Blob Storage, and Celery connectivity.
"""

import asyncio
import os
import sys
import tempfile
import uuid
from typing import AsyncIterator

from dotenv import load_dotenv
import redis.asyncio as redis

from careintel.core.config import get_settings
from careintel.core.database import check_database_liveness, build_engine
from careintel.infrastructure.storage.azure_provider import AzureBlobProvider


async def dummy_stream(data: bytes, chunk_size: int = 1024) -> AsyncIterator[bytes]:
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


async def test_postgres(settings) -> bool:
    print("\n--- Testing PostgreSQL / Supabase ---")
    engine = build_engine(settings)
    try:
        is_live = await check_database_liveness(engine)
        if is_live:
            print("PASS (SELECT 1 succeeded)")
            return True
        else:
            print("FAIL (SELECT 1 failed)")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False
    finally:
        await engine.dispose()


async def test_redis(settings) -> bool:
    print("\n--- Testing Redis ---")
    redis_url = settings.redis_url.get_secret_value() if settings.redis_url else None
    if not redis_url:
        print("SKIP: REDIS_URL not configured")
        return False
        
    try:
        r = redis.from_url(redis_url)
        await r.ping()
        print("PASS (PING succeeded)")
        await r.aclose()
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


async def test_celery_broker() -> bool:
    print("\n--- Testing Celery Broker ---")
    try:
        # Import celery app
        from careintel.workers.celery_app import celery_app
        
        # We can test broker connection by creating a connection
        with celery_app.connection_for_write() as conn:
            conn.connect()
            print("PASS (Broker connected)")
            return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


async def test_blob_storage(settings) -> bool:
    print("\n--- Testing Azure Blob Storage ---")
    connection_string = settings.azure_storage_connection_string
    if not connection_string:
        print("SKIP: AZURE_STORAGE_CONNECTION_STRING not configured")
        return False
        
    provider = AzureBlobProvider(
        connection_string=connection_string.get_secret_value(),
        container_name=settings.azure_storage_container,
    )
    
    test_key = f"careintel-verify/{uuid.uuid4()}/test.txt"
    test_content = b"Verification payload"
    
    # 1. Container verification
    try:
        await provider.ensure_container()
        print("Container check: PASS")
    except Exception as e:
        print(f"FAIL (Container check): {e}")
        return False

    # 2. Upload
    try:
        stream = dummy_stream(test_content)
        await provider.upload(test_key, stream, "text/plain", len(test_content))
        print("Upload: PASS")
    except Exception as e:
        print(f"FAIL (Upload): {e}")
        return False
        
    # 3. Download
    try:
        downloaded = b""
        async for chunk in provider.download(test_key):
            downloaded += chunk
            
        if downloaded == test_content:
            print("Download verification: PASS")
        else:
            print("FAIL (Download verification: Content mismatch)")
            return False
    except Exception as e:
        print(f"FAIL (Download): {e}")
        return False
        
    # 4. Delete
    try:
        await provider.delete(test_key)
        exists = await provider.exists(test_key)
        if not exists:
            print("Delete verification: PASS")
        else:
            print("FAIL (Delete verification: Blob still exists)")
            return False
    except Exception as e:
        print(f"FAIL (Delete): {e}")
        return False

    return True


async def main() -> None:
    # Do not enforce production constraints for the script itself unless we explicitly set it
    # We load standard env
    load_dotenv()
    settings = get_settings()
    
    print("="*60)
    print("CAREINTEL INFRASTRUCTURE VERIFICATION")
    print("="*60)
    
    results = {
        "PostgreSQL": await test_postgres(settings),
        "Redis": await test_redis(settings),
        "Celery Broker": await test_celery_broker(),
        "Azure Blob Storage": await test_blob_storage(settings)
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    all_pass = True
    for k, v in results.items():
        status = "PASS" if v else "FAIL/SKIPPED"
        if not v:
            all_pass = False
        print(f"{k.ljust(20)}: {status}")
        
    if not all_pass:
        print("\nNote: Skipped tests count as FAIL for the overall run if credentials were not provided.")
        sys.exit(1)
    else:
        print("\nAll infrastructure checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
