"""
Demo Translation Provider.
"""

from careintel.infrastructure.translation.port import TranslationProvider


class DemoTranslationProvider(TranslationProvider):
    """
    Deterministic fake Translation provider for testing.
    """

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text
        return f"[Translated to {target_language}] {text}"
