"""Persisted transactional-outbox and durable-task recovery verification."""

from __future__ import annotations

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from careintel.application.workflow.outbox_dispatcher import (
    DispatchStatus,
    UnifiedOutboxDispatcher,
)
from careintel.application.workflow.task_service import AsyncTaskService
from careintel.core.config import Settings
from careintel.core.database import build_engine
from careintel.core.errors import ServiceUnavailableError
from careintel.domain.auth.models import UserContext
from careintel.domain.workflow.task_states import AsyncTaskStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM, CaseOutboxORM
from careintel.persistence.models.user import UserORM
from careintel.persistence.models.workflow import AsyncTaskORM
from careintel.persistence.repositories.task_repo import AsyncTaskRepository
from careintel.workers.executor import (
    PermanentTaskError,
    RetryableTaskError,
    execute_durable_task,
)

pytestmark = pytest.mark.integration


async def test_outbox_dispatch_retry_replay_and_duplicate_claim(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise durable state around broker publication without retaining rows."""
    if "test:test@" in settings.database_url.get_secret_value():
        pytest.skip("R4 integration test requires configured PostgreSQL.")

    engine = build_engine(settings)
    connection = await engine.connect()
    outer = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    actor_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    case_id = uuid.uuid4()
    event_id = f"000000000000000000000{uuid.uuid4().hex[:5]}"
    correlation_id = f"r4-{uuid.uuid4()}"
    session = session_factory()
    try:
        session.add_all(
            [
                UserORM(
                    id=actor_id,
                    email=f"r4-actor-{actor_id}@example.invalid",
                    display_name="Synthetic R4 Actor",
                    password_hash="synthetic-not-a-credential",
                    is_active=True,
                ),
                UserORM(
                    id=subject_id,
                    email=f"r4-subject-{subject_id}@example.invalid",
                    display_name="Synthetic R4 Subject",
                    password_hash="synthetic-not-a-credential",
                    is_active=True,
                ),
            ]
        )
        await session.flush()
        session.add(
            CaseORM(
                id=case_id,
                synthetic_subject_id=subject_id,
                facility_id=uuid.uuid4(),
                state="INPUT_RECEIVED",
                version=1,
                opened_by=actor_id,
            )
        )
        await session.flush()
        session.add(
            CaseOutboxORM(
                id=event_id,
                event_type="RETRIEVAL_REQUESTED",
                event_version=1,
                occurred_at=datetime.datetime(1900, 1, 1),
                producer="careintel.test",
                correlation_id=correlation_id,
                case_id=case_id,
                actor_id=actor_id,
                aggregate_version=1,
                payload={"entity_id": str(case_id), "entity_type": "case"},
            )
        )
        await session.commit()

        broker_send = MagicMock()
        monkeypatch.setattr(
            "careintel.application.workflow.outbox_dispatcher.celery_app.send_task",
            broker_send,
        )
        dispatcher = UnifiedOutboxDispatcher(session_factory, dispatcher_id="synthetic-r4")
        dispatcher._MODELS = {"case": CaseOutboxORM}

        assert await dispatcher.dispatch_once(batch_size=1) == 1
        persisted = await session.get(CaseOutboxORM, event_id, populate_existing=True)
        assert persisted is not None
        assert persisted.dispatch_status == DispatchStatus.DISPATCHED
        assert persisted.published_at is not None
        assert persisted.celery_task_id is not None
        broker_send.assert_called_once_with(
            "careintel.tasks.retrieval.run_retrieval",
            kwargs={"task_id": persisted.celery_task_id},
            task_id=persisted.celery_task_id,
            queue="careintel_retrieval",
        )

        task_id = uuid.UUID(persisted.celery_task_id)
        task_service = AsyncTaskService(AsyncTaskRepository(session))
        first_claim = await task_service.claim_for_execution(task_id, persisted.celery_task_id)
        assert first_claim is not None
        await session.commit()
        duplicate_claim = await task_service.claim_for_execution(task_id, persisted.celery_task_id)
        assert duplicate_claim is None
        await task_service.record_retry(task_id, "SyntheticTransientError", "sanitized")
        await session.commit()
        retry_claim = await task_service.claim_for_execution(task_id, persisted.celery_task_id)
        assert retry_claim is not None
        await task_service.record_success(task_id, {"durable": True})
        await session.commit()
        terminal_duplicate = await task_service.claim_for_execution(
            task_id, persisted.celery_task_id
        )
        assert terminal_duplicate is None

        task = await session.get(AsyncTaskORM, task_id, populate_existing=True)
        assert task is not None
        assert task.status == AsyncTaskStatus.SUCCEEDED.value
        assert task.attempt_count == 2
        assert task.result_json == {"durable": True}
        assert (
            await session.scalar(
                select(func.count())
                .select_from(AsyncTaskORM)
                .where(AsyncTaskORM.idempotency_key == f"outbox_{event_id}")
            )
            == 1
        )

        persisted.published_at = None
        persisted.dispatch_status = DispatchStatus.FAILED
        persisted.dispatch_attempts = persisted.max_dispatch_attempts
        persisted.last_error_category = "SyntheticBrokerFailure"
        await session.commit()
        await dispatcher.replay("case", event_id, actor_id)
        replayed = await session.get(CaseOutboxORM, event_id, populate_existing=True)
        assert replayed is not None
        assert replayed.dispatch_status == DispatchStatus.PENDING
        assert replayed.dispatch_attempts == 0
        assert replayed.last_error_category is None
    finally:
        await session.close()
        await outer.rollback()
        await connection.close()
        await engine.dispose()


async def test_durable_executor_bounds_retries_and_sanitizes_failure(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    if "test:test@" in settings.database_url.get_secret_value():
        pytest.skip("R4 integration test requires configured PostgreSQL.")

    engine = build_engine(settings)
    connection = await engine.connect()
    outer = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    actor_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    case_id = uuid.uuid4()
    task_id = uuid.uuid4()
    correlation_id = f"r4-retry-{uuid.uuid4()}"
    payload = {
        "task_type": "careintel.tasks.synthetic.transient",
        "task_version": 1,
        "entity_type": "case",
        "entity_id": str(case_id),
        "case_id": str(case_id),
        "actor_id": str(actor_id),
        "correlation_id": correlation_id,
        "config": {},
    }
    session = session_factory()
    try:
        session.add_all(
            [
                UserORM(
                    id=actor_id,
                    email=f"r4-retry-actor-{actor_id}@example.invalid",
                    display_name="Synthetic Retry Actor",
                    password_hash="synthetic-not-a-credential",
                    is_active=True,
                ),
                UserORM(
                    id=subject_id,
                    email=f"r4-retry-subject-{subject_id}@example.invalid",
                    display_name="Synthetic Retry Subject",
                    password_hash="synthetic-not-a-credential",
                    is_active=True,
                ),
            ]
        )
        await session.flush()
        session.add(
            CaseORM(
                id=case_id,
                synthetic_subject_id=subject_id,
                facility_id=uuid.uuid4(),
                state="INPUT_RECEIVED",
                version=1,
                opened_by=actor_id,
            )
        )
        await session.flush()
        session.add(
            AsyncTaskORM(
                id=task_id,
                task_type="careintel.tasks.synthetic.transient",
                task_version=1,
                idempotency_key=f"synthetic-retry-{task_id}",
                case_id=case_id,
                entity_type="case",
                entity_id=case_id,
                actor_id=actor_id,
                correlation_id=correlation_id,
                status=AsyncTaskStatus.PENDING.value,
                attempt_count=0,
                max_attempts=3,
                payload_json=payload,
            )
        )
        await session.commit()

        actor = UserContext(
            id=actor_id,
            is_active=True,
            roles={"synthetic-worker-actor"},
            permissions=set(),
            role_facilities={},
        )
        monkeypatch.setattr(
            "careintel.workers.executor.get_session_factory", lambda: session_factory
        )
        monkeypatch.setattr(
            "careintel.workers.executor.load_worker_actor", AsyncMock(return_value=actor)
        )

        async def transient_handler(*_args: object) -> dict[str, object]:
            raise ServiceUnavailableError("synthetic sensitive narrative must not persist")

        with pytest.raises(RetryableTaskError):
            await execute_durable_task(str(task_id), transient_handler)
        with pytest.raises(RetryableTaskError):
            await execute_durable_task(str(task_id), transient_handler)
        with pytest.raises(PermanentTaskError):
            await execute_durable_task(str(task_id), transient_handler)

        task = await session.get(AsyncTaskORM, task_id, populate_existing=True)
        assert task is not None
        assert task.status == AsyncTaskStatus.FAILED.value
        assert task.attempt_count == 3
        assert task.error_category == "ServiceUnavailableError"
        assert task.failure_reason == "ServiceUnavailableError"
        assert "sensitive" not in task.failure_reason
        audits = (
            (
                await session.execute(
                    select(AuditLogORM).where(AuditLogORM.correlation_id == correlation_id)
                )
            )
            .scalars()
            .all()
        )
        assert [item.event_type for item in audits].count("task_retrying") == 2
        assert [item.event_type for item in audits].count("task_failed") == 1
        assert "sensitive" not in str([item.detail for item in audits])
    finally:
        await session.close()
        await outer.rollback()
        await connection.close()
        await engine.dispose()
