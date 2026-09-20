"""
Demo Language Provider.
"""

from careintel.infrastructure.language.port import LanguageDetectionResult, LanguageProvider


class DemoLanguageProvider(LanguageProvider):
    """
    Deterministic fake Language Detection provider for testing.
    """

    async def detect_language(self, text: str) -> list[LanguageDetectionResult]:
        return [LanguageDetectionResult(language="en", confidence=0.99)]
