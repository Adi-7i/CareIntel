"""Bounded startup behavior for unavailable external dependencies."""

from __future__ import annotations

import asyncio
import time

import pytest

from careintel.core.errors import StorageError


@pytest.mark.unit
@pytest.mark.asyncio
async def test_blob_startup_initialization_has_hard_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed = False

    class HangingBlobProvider:
        def __init__(self, **_kwargs: object) -> None:
            pass

        async def ensure_container(self) -> None:
            await asyncio.Event().wait()

        async def close(self) -> None:
            nonlocal closed
            closed = True

    monkeypatch.setenv("AZURE_STORAGE_CONNECTION_STRING", "synthetic-connection-string")
    monkeypatch.setenv("DEPENDENCY_CONNECT_TIMEOUT_SECONDS", "0.1")
    from careintel.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr("careintel.main.AzureBlobProvider", HangingBlobProvider)
    from careintel.main import create_app

    app = create_app()
    started = time.perf_counter()
    with pytest.raises(StorageError, match="timed out"):
        async with app.router.lifespan_context(app):
            pass

    assert time.perf_counter() - started < 0.5
    assert closed is True
