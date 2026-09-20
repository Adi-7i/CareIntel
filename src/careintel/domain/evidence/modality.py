"""
Evidence modality enum.
"""

from enum import StrEnum


class EvidenceModality(StrEnum):
    """Supported modalities for evidence intake."""

    TEXT = "text"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
