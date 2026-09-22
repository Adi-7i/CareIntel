"""
Processor type enum.
"""

from enum import StrEnum


class ProcessorType(StrEnum):
    """Types of processing that can be run on evidence."""

    DOCUMENT_OCR = "document_ocr"
    SPEECH_TRANSCRIPTION = "speech_transcription"
    LANGUAGE_NORMALIZATION = "language_normalization"
    CANDIDATE_EXTRACTION = "candidate_extraction"
