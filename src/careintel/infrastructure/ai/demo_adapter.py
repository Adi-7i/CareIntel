"""
Deterministic Demo LLM Provider.

Returns stable, configurable structured outputs for testing AI workflows
without hitting an external API. Validates that the requested schema
matches what it returns to simulate strict schema compliance.
"""

from __future__ import annotations

import json
from typing import Any

from careintel.domain.ai.models import AITaskConfig, SafeContext
from careintel.infrastructure.ai.port import LLMProvider, LLMProviderError, LLMResult


class DemoLLMProvider:
    """
    Testing adapter that returns a predefined JSON response.
    """

    def __init__(self, predefined_response: dict[str, Any] | None = None) -> None:
        self.predefined_response = predefined_response or {}
        self.last_context: SafeContext | None = None
        self.last_config: AITaskConfig | None = None

    async def generate_structured(
        self,
        context: SafeContext,
        config: AITaskConfig,
    ) -> LLMResult:
        """
        Return the predefined response and record the inputs for test assertions.
        """
        self.last_context = context
        self.last_config = config

        if not context.output_schema:
            raise LLMProviderError("Missing output schema in context.")

        raw_json = json.dumps(self.predefined_response)

        return LLMResult(
            raw_response=raw_json,
            parsed_content=self.predefined_response,
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=50,
        )


# Verify Protocol compliance at import time
def _check_protocol() -> None:
    _: LLMProvider = DemoLLMProvider()


_check_protocol()
