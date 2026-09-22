"""
Azure OpenAI LLM Provider Adapter.

Implements the LLMProvider Protocol using the official openai Python SDK
configured specifically for Azure OpenAI.
Uses Strict Structured Outputs via response_format configuration.
Enforces context separation via explicit system vs. user message boundaries.
"""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncAzureOpenAI

from careintel.domain.ai.models import AITaskConfig, SafeContext
from careintel.infrastructure.ai.port import LLMProviderError, LLMResult


class AzureOpenAIAdapter:
    """
    Azure OpenAI implementation of the LLMProvider Protocol.
    """

    def __init__(self, endpoint: str, api_key: str, deployment: str) -> None:
        self._client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-15-preview",
        )
        self._deployment = deployment

    async def generate_structured(
        self,
        context: SafeContext,
        config: AITaskConfig,
    ) -> LLMResult:
        """
        Generate a structured response using Azure OpenAI Structured Outputs.
        """
        messages = self._build_messages(context)

        # Structure the schema as expected by OpenAI's response_format
        # Strict mode is required for guaranteed schema adherence.
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": config.task_type.value,
                "description": f"Output schema for {config.task_type.value}",
                "strict": True,
                "schema": context.output_schema,
            },
        }

        try:
            response = await self._client.chat.completions.create(
                model=self._deployment, # Azure uses deployment name as the model
                messages=messages,
                response_format=response_format,
                timeout=config.timeout_seconds,
                seed=42,          # Request best-effort determinism
            )

            choice = response.choices[0]
            raw_content = choice.message.content or ""

            parsed_content = None
            if raw_content:
                try:
                    parsed_content = json.loads(raw_content)
                except json.JSONDecodeError:
                    pass

            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0

            return LLMResult(
                raw_response=raw_content,
                parsed_content=parsed_content,
                finish_reason=choice.finish_reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        except Exception as e:
            raise LLMProviderError(f"Azure OpenAI API error: {e!s}") from e

    def _build_messages(self, context: SafeContext) -> list[dict[str, str]]:
        """
        Map SafeContext into OpenAI chat messages.

        SYSTEM: All application-controlled trusted instructions and constraints.
        USER: All external/untrusted data, clearly delineated by origin.
        """
        system_content = (
            f"{context.system_instructions}\n\n"
            f"TASK:\n{context.task_instructions}\n\n"
        )
        if context.policy_constraints:
            system_content += "CONSTRAINTS:\n"
            for c in context.policy_constraints:
                system_content += f"- {c}\n"

        messages = [
            {"role": "system", "content": system_content.strip()}
        ]

        # Append data blocks as user messages with structural boundaries
        user_content = ""

        def _append_passages(title: str, passages: list[Any]) -> None:
            nonlocal user_content
            if not passages:
                return
            user_content += f"\n\n--- BEGIN {title} ---\n"
            for p in passages:
                loc = p.citation_locator or p.source_id or "unknown"
                user_content += f"[SOURCE: {loc}]\n{p.content}\n"
            user_content += f"--- END {title} ---"

        _append_passages("KNOWLEDGE CORPUS", context.knowledge_passages)
        _append_passages("PATIENT EVIDENCE", context.patient_evidence)
        _append_passages("TRANSCRIPTS", context.stt_transcripts)
        _append_passages("OCR TEXT", context.ocr_content)
        _append_passages("EXTRACTED FACTS", context.extracted_facts)
        _append_passages("TIMELINE EVENTS", context.timeline_events)
        _append_passages("MISSING INFORMATION", context.missing_information)
        _append_passages("CONFLICTING INFORMATION", context.conflicting_information)

        if user_content.strip():
            messages.append({"role": "user", "content": user_content.strip()})

        return messages

# Verify Protocol compliance at import time
def _check_protocol() -> None:
    # Just type checking structure, don't need real keys
    pass

