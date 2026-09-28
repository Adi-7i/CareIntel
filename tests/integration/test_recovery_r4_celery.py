"""Real Redis/Celery execution of one synthetic CareIntel business task."""

from __future__ import annotations

import asyncio
import datetime
import uuid

import pytest
from celery.contrib.testing.worker import start_worker
from sqlalchemy import delete

from careintel.core.config import Settings
from careintel.core.database import build_engine, build_session_factory
from careintel.domain.workflow.models import AsyncTaskPayload
from careintel.domain.workflow.task_states import AsyncTaskStatus
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM, CaseOutboxORM
from careintel.persistence.models.handoff import HandoffORM, RecipientORM, ReferralPackageORM
from careintel.persistence.models.user import UserORM
from careintel.persistence.models.workflow import AsyncTaskORM
from careintel.workers.celery_app import celery_app

pytestmark = pytest.mark.integration


async def test_real_celery_handoff_task_is_durable_and_idempotent(settings: Settings) -> None:
    """Use a unique queue so no unrelated shared-broker messages are consumed."""
    if "test:test@" in settings.database_url.get_secret_value():
        pytest.skip("Celery integration test requires configured PostgreSQL.")
    if settings.redis_url is None:
        pytest.skip("Celery integration test requires configured Redis.")

    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    actor_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    case_id = uuid.uuid4()
    recipient_id = uuid.uuid4()
    package_id = uuid.uuid4()
    handoff_id = uuid.uuid4()
    task_id = uuid.uuid4()
    correlation_id = f"r4-celery-{uuid.uuid4()}"
    queue_name = f"careintel_verify_{uuid.uuid4().hex}"
    payload = AsyncTaskPayload(
        task_type="careintel.tasks.handoff.deliver_handoff",
        task_version=1,
        entity_type="handoff",
        entity_id=handoff_id,
        case_id=case_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
        config={"handoff_id": str(handoff_id)},
    )

    try:
        async with session_factory() as session:
            session.add_all(
                [
                    UserORM(
                        id=actor_id,
                        email=f"r4-celery-actor-{actor_id}@example.invalid",
                        display_name="Synthetic Celery Actor",
                        password_hash="synthetic-not-a-credential",
                        is_active=True,
                    ),
                    UserORM(
                        id=subject_id,
                        email=f"r4-celery-subject-{subject_id}@example.invalid",
                        display_name="Synthetic Celery Subject",
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
                    state="REVIEWED",
                    version=1,
                    opened_by=actor_id,
                )
            )
            session.add(
                RecipientORM(
                    id=recipient_id,
                    name="Synthetic Celery Recipient",
                    recipient_type="synthetic-channel",
                    config_json={"provider": "demo"},
                    is_active=True,
                )
            )
            await session.flush()
            session.add(
                ReferralPackageORM(
                    id=package_id,
                    case_id=case_id,
                    version=1,
                    prepared_by=actor_id,
                    content_json={"synthetic": True},
                    evidence_ids=[],
                    status="FINALIZED",
                    correlation_id=correlation_id,
                )
            )
            await session.flush()
            session.add(
                HandoffORM(
                    id=handoff_id,
                    case_id=case_id,
                    referral_package_id=package_id,
                    recipient_id=recipient_id,
                    channel="synthetic-channel",
                    status="READY",
                    idempotency_key=f"synthetic-{handoff_id}",
                    sent_by=actor_id,
                    correlation_id=correlation_id,
                    version=1,
                )
            )
            session.add(
                AsyncTaskORM(
                    id=task_id,
                    task_type=payload.task_type,
                    task_version=1,
                    idempotency_key=f"synthetic-celery-{task_id}",
                    case_id=case_id,
                    entity_type="handoff",
                    entity_id=handoff_id,
                    actor_id=actor_id,
                    correlation_id=correlation_id,
                    status=AsyncTaskStatus.QUEUED.value,
                    max_attempts=3,
                    celery_task_id=str(task_id),
                    payload_json=payload.to_dict(),
                    queued_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
                )
            )
            await session.commit()

        with start_worker(
            celery_app,
            pool="solo",
            queues=[queue_name],
            perform_ping_check=False,
            loglevel="WARNING",
        ):
            celery_app.send_task(
                payload.task_type,
                kwargs={"task_id": str(task_id)},
                task_id=str(task_id),
                queue=queue_name,
            )

            deadline = asyncio.get_running_loop().time() + 60
            terminal: AsyncTaskORM | None = None
            while asyncio.get_running_loop().time() < deadline:
                async with session_factory() as session:
                    terminal = await session.get(AsyncTaskORM, task_id)
                    if terminal is not None and terminal.status in {
                        AsyncTaskStatus.SUCCEEDED.value,
                        AsyncTaskStatus.FAILED.value,
                    }:
                        break
                await asyncio.sleep(0.25)

            assert terminal is not None
            assert terminal.status == AsyncTaskStatus.SUCCEEDED.value
            assert terminal.attempt_count == 1
            assert terminal.result_json is not None
            assert terminal.result_json["status"] == "SENT"

            async with session_factory() as session:
                handoff = await session.get(HandoffORM, handoff_id)
                case = await session.get(CaseORM, case_id)
                assert handoff is not None and handoff.status == "SENT"
                assert handoff.attempt_count == 1
                assert case is not None and case.state == "REFERRED"

            celery_app.send_task(
                payload.task_type,
                kwargs={"task_id": str(task_id)},
                task_id=f"duplicate-{task_id}",
                queue=queue_name,
            )
            await asyncio.sleep(1.0)
            async with session_factory() as session:
                duplicate = await session.get(AsyncTaskORM, task_id)
                handoff = await session.get(HandoffORM, handoff_id)
                assert duplicate is not None and duplicate.attempt_count == 1
                assert handoff is not None and handoff.attempt_count == 1
    finally:
        async with session_factory() as session:
            await session.execute(
                delete(AuditLogORM).where(AuditLogORM.correlation_id == correlation_id)
            )
            await session.execute(delete(CaseOutboxORM).where(CaseOutboxORM.case_id == case_id))
            await session.execute(delete(CaseORM).where(CaseORM.id == case_id))
            await session.execute(delete(RecipientORM).where(RecipientORM.id == recipient_id))
            await session.execute(delete(UserORM).where(UserORM.id.in_([actor_id, subject_id])))
            await session.commit()
        await engine.dispose()
