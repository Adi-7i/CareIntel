"""
Speech to Text Provider interface.
"""

from typing import Protocol

from careintel.domain.processing.processing_models import TranscriptSegment


class SpeechResult:
    """Standardized Speech-to-Text output."""

    def __init__(self, segments: list[TranscriptSegment], provider_version: str) -> None:
        self.segments = segments
        self.provider_version = provider_version


class SpeechProvider(Protocol):
    """Protocol for STT adapters."""

    async def process_audio(self, file_path: str, run_id: str) -> SpeechResult:
        """
        Process an audio file and return standardized STT output.
        """
        ...
