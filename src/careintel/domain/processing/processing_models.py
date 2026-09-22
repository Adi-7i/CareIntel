"""
Domain models for Multimodal Processing Engine.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field

from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.processing.processor_type import ProcessorType


@dataclass(frozen=True)
class ProcessingRunRecord:
    """Core aggregate for a processing attempt."""

    run_id: uuid.UUID
    evidence_id: uuid.UUID
    processor_type: ProcessorType
    provider: str
    status: ProcessingStatus
    config_version: str
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    failure_reason: str | None = None


# ── Document / OCR ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OcrPage:
    """A single page of OCR output."""

    page_id: uuid.UUID
    run_id: uuid.UUID
    page_number: int
    width: float | None = None
    height: float | None = None
    unit: str | None = None
    confidence: float | None = None
    status: str = "SUCCESS"  # SUCCESS, FAILED


@dataclass(frozen=True)
class OcrRegion:
    """A bounded region of text on a page."""

    region_id: uuid.UUID
    page_id: uuid.UUID
    text: str
    reading_order: int
    bounding_box: list[float] | None = None  # [x1, y1, x2, y2, ...]
    confidence: float | None = None


# ── Audio / STT ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TranscriptSegment:
    """A time-bounded segment of transcribed speech."""

    segment_id: uuid.UUID
    run_id: uuid.UUID
    start_time_ms: int
    end_time_ms: int
    text: str
    language: str | None = None
    confidence: float | None = None
    speaker_label: str | None = None
    is_silence: bool = False


# ── Language & Translation ──────────────────────────────────────────────────


@dataclass(frozen=True)
class LanguageResult:
    """Language detection and optional translation result."""

    result_id: uuid.UUID
    run_id: uuid.UUID
    detected_language: str | None
    detected_confidence: float | None
    normalized_text: str
    translation_text: str | None = None
    translation_provider: str | None = None


# ── Structured Extraction ───────────────────────────────────────────────────


@dataclass(frozen=True)
class ExtractionProvenance:
    """Pointer back to original evidence span/region/segment."""

    evidence_id: uuid.UUID
    page_number: int | None = None
    region_id: uuid.UUID | None = None
    segment_id: uuid.UUID | None = None
    span_start: int | None = None
    span_end: int | None = None
    raw_source_text: str | None = None


@dataclass(frozen=True)
class CandidateField:
    """An extracted candidate structured field."""

    candidate_id: uuid.UUID
    run_id: uuid.UUID
    field_type: str  # e.g., 'symptom', 'medication', 'onset'
    value: str
    normalized_value: str | None = None
    confidence: float | None = None
    status: str = "CANDIDATE"  # CANDIDATE, VERIFIED, REJECTED
    provenance: list[ExtractionProvenance] = field(default_factory=list)
