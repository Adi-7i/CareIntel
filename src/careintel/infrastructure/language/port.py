"""
Language Provider interface.
"""

from typing import Protocol


class LanguageDetectionResult:
    def __init__(self, language: str, confidence: float) -> None:
        self.language = language
        self.confidence = confidence


class LanguageProvider(Protocol):
    """Protocol for Language Detection adapters."""

    async def detect_language(self, text: str) -> list[LanguageDetectionResult]:
        """
        Detect language of a given text.
        Returns candidates ordered by confidence.
        """
        ...
