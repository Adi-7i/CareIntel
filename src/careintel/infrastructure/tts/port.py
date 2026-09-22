"""
Text-to-Speech Provider interface.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TTSResult:
    """Standardized Text-to-Speech output."""
    audio_bytes: bytes
    audio_format: str      # e.g., "mp3", "wav", "opus"
    provider: str
    model: str
    voice: str


class TTSProvider(Protocol):
    """Protocol for TTS adapters."""

    async def synthesize(self, text: str, voice: str | None = None) -> TTSResult:
        """
        Synthesize text into speech audio bytes.
        """
        ...
