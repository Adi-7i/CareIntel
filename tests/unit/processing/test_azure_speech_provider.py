from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

from careintel.infrastructure.stt import azure_provider
from careintel.infrastructure.stt.azure_provider import AzureSpeechProvider


class _Response:
    status_code = 200
    text = ""

    def json(self) -> dict[str, Any]:
        return {
            "language": "en",
            "segments": [
                {
                    "start": 0.25,
                    "end": 1.5,
                    "text": "Synthetic speech.",
                    "speaker": "speaker_0",
                }
            ],
        }


class _CapturingClient:
    request_data: dict[str, str] | None = None

    def __init__(self, *, timeout: float) -> None:
        assert timeout == 300.0

    async def __aenter__(self) -> _CapturingClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def post(
        self,
        _url: str,
        *,
        headers: dict[str, str],
        data: dict[str, str],
        files: dict[str, tuple[str, Any, str]],
    ) -> _Response:
        assert headers == {"api-key": "test-key"}
        assert files["file"][0] == "synthetic.mp3"
        type(self).request_data = data
        return _Response()


@pytest.mark.parametrize(
    ("mode", "expected_format"),
    [("transcribe", "json"), ("diarize", "diarized_json")],
)
async def test_request_format_matches_speech_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode: str,
    expected_format: str,
) -> None:
    audio_path = tmp_path / "synthetic.mp3"
    audio_path.write_bytes(b"synthetic-audio")
    monkeypatch.setattr(azure_provider.httpx, "AsyncClient", _CapturingClient)

    provider = AzureSpeechProvider(
        endpoint="https://example.invalid",
        api_key="test-key",
        api_version="2025-03-01-preview",
        deployment="synthetic-deployment",
        mode=mode,  # type: ignore[arg-type]
    )
    result = await provider.process_audio(str(audio_path), str(uuid.uuid4()))

    assert _CapturingClient.request_data == {"response_format": expected_format}
    assert result.segments[0].speaker_label == "speaker_0"
    assert result.segments[0].text == "Synthetic speech."
