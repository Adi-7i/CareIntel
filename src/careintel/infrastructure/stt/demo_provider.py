"""
Demo Speech Provider.
"""

import uuid

from careintel.domain.processing.processing_models import TranscriptSegment
from careintel.infrastructure.stt.port import SpeechProvider, SpeechResult


class DemoSpeechProvider(SpeechProvider):
    """
    Deterministic fake STT provider for testing.
    """

    async def process_audio(self, file_path: str, run_id: str) -> SpeechResult:
        run_uuid = uuid.UUID(run_id)

        segment = TranscriptSegment(
            segment_id=uuid.uuid4(),
            run_id=run_uuid,
            start_time_ms=0,
            end_time_ms=5000,
            text="Demo audio transcript segment.",
            language="en",
            confidence=0.98,
        )

        return SpeechResult(
            segments=[segment],
            provider_version="demo-stt-v1",
        )
