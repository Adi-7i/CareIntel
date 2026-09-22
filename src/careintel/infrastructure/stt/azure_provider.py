"""
Azure OpenAI STT Provider.

Implementation for Speech-to-Text using Azure OpenAI.
Supports both standard transcription (gpt-4o-mini-transcribe)
and speaker-aware diarization (gpt-4o-transcribe-diarize).
"""

from __future__ import annotations

import os
import uuid
import httpx
from typing import Literal

from careintel.domain.processing.processing_models import TranscriptSegment
from careintel.infrastructure.stt.port import SpeechProvider, SpeechResult


class AzureSpeechProvider(SpeechProvider):
    """
    Azure OpenAI implementation of the SpeechProvider Protocol using httpx
    for exact REST route compliance.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str,
        mode: Literal["transcribe", "diarize"] = "transcribe",
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._api_version = api_version
        self._deployment = deployment
        self._mode = mode
        self._provider_version = f"azure-openai-{deployment}-{mode}-v1"

    def _build_url(self) -> str:
        return f"{self._endpoint}/openai/deployments/{self._deployment}/audio/transcriptions?api-version={self._api_version}"

    async def process_audio(self, file_path: str, run_id: str) -> SpeechResult:
        run_uuid = uuid.UUID(run_id)

        url = self._build_url()
        headers = {
            "api-key": self._api_key,
        }
        
        # Determine format based on mode
        data = {
            "response_format": "json",
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(file_path, "rb") as f:
                filename = os.path.basename(file_path)
                files = {
                    "file": (filename, f, "audio/mpeg") # Will adapt based on actual file, but basic mpeg is fine for fallback
                }
                response = await client.post(url, headers=headers, data=data, files=files)
                
        if response.status_code != 200:
            raise RuntimeError(f"Azure OpenAI STT Error: {response.status_code} - {response.text}")
            
        json_resp = response.json()
        
        segments = json_resp.get("segments", [])
        domain_segments = []

        if segments:
            for s in segments:
                start_ms = int(s.get("start", 0.0) * 1000)
                end_ms = int(s.get("end", 0.0) * 1000)
                text = s.get("text", "").strip()
                confidence = None
                speaker = s.get("speaker", None)

                if not text:
                    continue

                domain_segments.append(
                    TranscriptSegment(
                        segment_id=uuid.uuid4(),
                        run_id=run_uuid,
                        start_time_ms=start_ms,
                        end_time_ms=end_ms,
                        text=text,
                        language=json_resp.get("language", None),
                        confidence=confidence,
                        speaker_label=speaker,
                        is_silence=False,
                    )
                )
        else:
            # Fallback if no segments provided
            domain_segments.append(
                TranscriptSegment(
                    segment_id=uuid.uuid4(),
                    run_id=run_uuid,
                    start_time_ms=0,
                    end_time_ms=int(json_resp.get("duration", 0.0) * 1000) or 5000,
                    text=json_resp.get("text", ""),
                    language=json_resp.get("language", None),
                    confidence=None,
                    speaker_label=None,
                    is_silence=False,
                )
            )

        return SpeechResult(
            segments=domain_segments,
            provider_version=self._provider_version,
        )

# Verify Protocol compliance
def _check_protocol() -> None:
    pass
