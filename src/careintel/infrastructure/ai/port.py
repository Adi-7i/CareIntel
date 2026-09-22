"""
LLM Provider Protocol.

Abstracts interaction with external Language Models.
Enforces Structured Outputs and SafeContext separation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from careintel.domain.ai.models import AITaskConfig, SafeContext


@dataclass(frozen=True)
class LLMResult:
    """
    Standardized output from an LLM provider.
    """
    raw_response: str
    parsed_content: dict[str, object] | None
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int


class LLMProviderError(Exception):
    """Base exception for LLM provider failures."""
    pass


class LLMProvider(Protocol):
    """
    Protocol for LLM adapters (e.g. OpenAI).

    Must support JSON schema structured outputs and system/user
    message separation based on the SafeContext definition.
    """

    async def generate_structured(
        self,
        context: SafeContext,
        config: AITaskConfig,
    ) -> LLMResult:
        """
        Generate a structured response strictly matching the schema.

        Args:
            context: SafeContext separating instructions from data.
            config: AITaskConfig defining model, provider, timeout.

        Returns:
            LLMResult containing the parsed dictionary and metadata.

        Raises:
            LLMProviderError: If generation or parsing fails.
        """
        ...
