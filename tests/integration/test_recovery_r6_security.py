"""Database-enforced R6 audit and trace-security verification."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from careintel.core.config import Settings
from careintel.core.correlation import (
    _causation_id_var,
    _request_id_var,
    _trace_source_var,
)
from careintel.core.database import build_engine
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.repositories.audit_repo import AuditRepository

pytestmark = pytest.mark.integration


async def test_audit_is_append_only_and_trace_metadata_is_sanitized(settings: Settings) -> None:
    if "test:test@" in settings.database_url.get_secret_value():
        pytest.skip("R6 integration test requires configured PostgreSQL.")

    engine = build_engine(settings)
    connection = await engine.connect()
    outer = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = session_factory()
    request_token = _request_id_var.set(f"request-{uuid.uuid4()}")
    causation_token = _causation_id_var.set(f"cause-{uuid.uuid4()}")
    source_token = _trace_source_var.set("integration-test")
    try:
        audit = await AuditRepository(session).append(
            AuditLogORM(
                event_type="synthetic_r6_security_event",
                actor_id=None,
                target_id=uuid.uuid4(),
                target_type="synthetic",
                correlation_id=f"r6-{uuid.uuid4()}",
                outcome="SUCCESS",
                detail={
                    "safe": "metadata",
                    "nested": {"api_key": "synthetic-secret-must-not-persist"},
                },
            )
        )
        await session.flush()
        audit_id = audit.id
        assert audit.request_id is not None
        assert audit.causation_id is not None
        assert audit.source == "integration-test"
        assert audit.detail == {
            "safe": "metadata",
            "nested": {"api_key": "[REDACTED]"},
        }

        for statement in (
            "UPDATE audit_logs SET outcome = 'MUTATED' WHERE id = :audit_id",
            "DELETE FROM audit_logs WHERE id = :audit_id",
        ):
            savepoint = await session.begin_nested()
            with pytest.raises(DBAPIError):
                await session.execute(text(statement), {"audit_id": audit_id})
            await savepoint.rollback()

        persisted = await session.scalar(
            select(AuditLogORM).where(AuditLogORM.id == audit_id)
        )
        assert persisted is not None
        assert persisted.outcome == "SUCCESS"
    finally:
        _request_id_var.reset(request_token)
        _causation_id_var.reset(causation_token)
        _trace_source_var.reset(source_token)
        await session.close()
        if outer.is_active:
            await outer.rollback()
        await connection.close()
        await engine.dispose()
