"""
Async Task ORM models.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from careintel.persistence.base import Base


class AsyncTaskORM(Base):
    """
    Durable execution identity for asynchronous background tasks.
    """

    __tablename__ = "async_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    task_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    # SHA-256 of (task_type + entity_id + case_id + config)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    correlation_id: Mapped[str] = mapped_column(String, nullable=False)
    causation_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # PENDING, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="PENDING", server_default=text("'PENDING'")
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default=text("3")
    )
    celery_task_id: Mapped[str | None] = mapped_column(String, nullable=True)

    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    queued_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    heartbeat_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_async_tasks_idempotency"),
        # Partial index for outbox dispatcher finding PENDING tasks
        Index(
            "ix_async_tasks_pending",
            "created_at",
            postgresql_where=text("status = 'PENDING'"),
        ),
        # Partial index for stale task recovery finding RUNNING tasks
        Index(
            "ix_async_tasks_running",
            "heartbeat_at",
            postgresql_where=text("status = 'RUNNING'"),
        ),
        Index("ix_async_tasks_case", "case_id"),
    )
