"""
Case ORM models.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from careintel.persistence.base import Base, TimestampMixin


class CaseORM(Base, TimestampMixin):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    synthetic_subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    facility_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    state: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    opened_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_cases_synthetic_subject", "synthetic_subject_id"),
        Index("ix_cases_facility_state", "facility_id", "state"),
    )


class EncounterORM(Base):
    __tablename__ = "encounters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    encounter_type: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )

    __table_args__ = (Index("ix_encounters_case_occurred", "case_id", "occurred_at"),)


class CaseStateHistoryORM(Base):
    __tablename__ = "case_state_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_state: Mapped[str] = mapped_column(String, nullable=False)
    to_state: Mapped[str] = mapped_column(String, nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    transitioned_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    command_type: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("ix_case_history_case_version", "case_id", "aggregate_version", unique=True),
    )


class CaseOutboxORM(Base):
    __tablename__ = "case_outbox"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        comment="ULID as primary key",
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    occurred_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    producer: Mapped[str] = mapped_column(String, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String, nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    published_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_case_outbox_unpublished", "id", postgresql_where=text("published_at IS NULL")),
    )
