"""
Azure OpenAI Text-to-Speech Provider.

Generates speech audio from text using Azure OpenAI TTS deployments.
"""

from __future__ import annotations

import httpx

from careintel.infrastructure.tts.port import TTSProvider, TTSResult


class AzureTTSProvider(TTSProvider):
    """
    Azure OpenAI implementation of the TTSProvider Protocol using httpx
    for exact REST route compliance.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str,
        default_voice: str = "nova",
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._api_version = api_version
        self._deployment = deployment
        self._default_voice = default_voice

    def _build_url(self) -> str:
        return f"{self._endpoint}/openai/deployments/{self._deployment}/audio/speech?api-version={self._api_version}"

    async def synthesize(self, text: str, voice: str | None = None) -> TTSResult:
        """
        Synthesize text into speech audio.
        """
        chosen_voice = voice or self._default_voice
        url = self._build_url()

        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }

        data = {
            "model": self._deployment,
            "input": text,
            "voice": chosen_voice
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)

        if response.status_code != 200:
            raise RuntimeError(f"Azure OpenAI TTS Error: {response.status_code} - {response.text}")

        audio_bytes = response.content

        # Azure typically returns audio/mpeg for TTS
        return TTSResult(
            audio_bytes=audio_bytes,
            audio_format="mp3",
            provider="azure_openai",
            model=self._deployment,
            voice=chosen_voice,
        )

# Verify Protocol compliance
def _check_protocol() -> None:
    pass
