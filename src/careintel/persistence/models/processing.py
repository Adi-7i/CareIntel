"""
Multimodal Processing ORM models.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from careintel.persistence.base import Base


class ProcessingRunORM(Base):
    __tablename__ = "processing_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    processor_type: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    config_version: Mapped[str] = mapped_column(String, nullable=False)

    started_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_processing_run_evidence", "evidence_id"),
        UniqueConstraint(
            "evidence_id", "processor_type", "config_version", name="uq_processing_run_idempotency"
        ),
    )


# ── OCR ────────────────────────────────────────────────────────────────────


class OcrPageORM(Base):
    __tablename__ = "ocr_pages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="SUCCESS")

    __table_args__ = (
        Index("ix_ocr_page_run", "run_id"),
        UniqueConstraint("run_id", "page_number", name="uq_ocr_page_number"),
    )


class OcrRegionORM(Base):
    __tablename__ = "ocr_regions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ocr_pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    reading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    # Stored as JSON array [x1, y1, x2, y2, ...]
    bounding_box: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (Index("ix_ocr_region_page", "page_id"),)


class OcrTableCandidateORM(Base):
    __tablename__ = "ocr_table_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ocr_pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    cells_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (Index("ix_ocr_table_page", "page_id"),)


# ── Audio / STT ────────────────────────────────────────────────────────────


class TranscriptRunORM(Base):
    __tablename__ = "transcript_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    processing_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    provider_version: Mapped[str] = mapped_column(String, nullable=False)


class TranscriptSegmentORM(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    transcript_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcript_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    speaker_label: Mapped[str | None] = mapped_column(String, nullable=True)
    is_silence: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (Index("ix_transcript_segment_run", "transcript_run_id"),)


# ── Language & Translation ─────────────────────────────────────────────────


class LanguageResultORM(Base):
    __tablename__ = "language_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    processing_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    detected_language: Mapped[str | None] = mapped_column(String, nullable=True)
    detected_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    translation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_provider: Mapped[str | None] = mapped_column(String, nullable=True)


# ── Structured Extraction ──────────────────────────────────────────────────


class ExtractionRunORM(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    processing_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    provider_version: Mapped[str] = mapped_column(String, nullable=False)


class ExtractedCandidateORM(Base):
    __tablename__ = "extracted_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extraction_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_type: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="CANDIDATE")

    # Store List of ExtractionProvenance domain objects as JSON array
    provenance_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )

    __table_args__ = (Index("ix_extracted_candidate_run", "extraction_run_id"),)
