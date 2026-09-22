"""
Translation Provider interface.
"""

from typing import Protocol


class TranslationProvider(Protocol):
    """Protocol for Translation adapters."""

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        """
        Translate text from source to target language.
        """
        ...
