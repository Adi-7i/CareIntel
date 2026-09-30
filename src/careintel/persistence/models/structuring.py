"""
Structuring ORM models.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Date, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from careintel.persistence.base import Base, TimestampMixin


class StructuringRunORM(Base):
    __tablename__ = "structuring_runs"

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
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extraction_runs.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("case_id", "extraction_run_id", name="uq_structuring_run_idempotency"),
    )


class TimelineEventORM(Base, TimestampMixin):
    __tablename__ = "timeline_events"

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
    structuring_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("structuring_runs.id"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    source_statement: Mapped[str] = mapped_column(Text, nullable=False)

    # Temporal Fields
    raw_temporal_expression: Mapped[str] = mapped_column(Text, nullable=False)
    temporal_precision: Mapped[str] = mapped_column(String, nullable=False)
    resolution_state: Mapped[str] = mapped_column(String, nullable=False)
    normalized_start: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    normalized_end: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    anchor_description: Mapped[str | None] = mapped_column(String, nullable=True)
    anchor_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
        nullable=True,
    )
    unresolved_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    # Ordering
    ordering_relation: Mapped[str] = mapped_column(String, nullable=False)
    ordering_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String, nullable=False)

    # Provenance
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_candidates.id"),
        nullable=False,
    )
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extraction_runs.id"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    __table_args__ = (
        Index("ix_timeline_event_case", "case_id"),
        Index("ix_timeline_event_evidence", "evidence_id"),
    )


class ConflictRecordORM(Base, TimestampMixin):
    __tablename__ = "conflict_records"

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
    field_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    detection_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("structuring_runs.id"),
        nullable=False,
    )

    __table_args__ = (Index("ix_conflict_record_case_field", "case_id", "field_type"),)


class ConflictCandidateLinkORM(Base, TimestampMixin):
    __tablename__ = "conflict_candidate_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    conflict_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conflict_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_candidates.id"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("conflict_id", "candidate_id", name="uq_conflict_candidate"),
    )


class ChecklistPolicyVersionORM(Base, TimestampMixin):
    __tablename__ = "checklist_policy_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    version_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class MissingInfoItemORM(Base, TimestampMixin):
    __tablename__ = "missing_info_items"

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
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("structuring_runs.id"),
        nullable=False,
    )
    requirement_key: Mapped[str] = mapped_column(String, nullable=False)
    checklist_version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    materiality: Mapped[str] = mapped_column(String, nullable=False)
    resolution: Mapped[str | None] = mapped_column(String, nullable=True)
    __table_args__ = (
        UniqueConstraint(
            "evaluation_run_id", "requirement_key", name="uq_missing_info_requirement"
        ),
    )


class ClarificationQuestionORM(Base, TimestampMixin):
    __tablename__ = "clarification_questions"

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
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("structuring_runs.id"),
        nullable=False,
    )
    requirement_key: Mapped[str] = mapped_column(String, nullable=False)
    missing_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("missing_info_items.id"),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    generator_version: Mapped[str] = mapped_column(String, nullable=False)
    __table_args__ = (
        UniqueConstraint("evaluation_run_id", "requirement_key", name="uq_question_requirement"),
    )
