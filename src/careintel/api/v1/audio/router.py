"""
FastAPI router for Audio and Speech capabilities.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from careintel.api.deps import get_current_user, get_speech_service
from careintel.application.audio.speech_service import SpeechService
from careintel.domain.auth.models import UserContext

router = APIRouter(prefix="/audio", tags=["audio"])


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., max_length=4096, description="Text to synthesize into speech")
    voice: str | None = Field(None, description="Optional voice to use for synthesis")


@router.post(
    "/speech",
    summary="Synthesize Speech",
    description="Generates audio speech from provided text using the configured TTS provider.",
    responses={
        200: {
            "content": {
                "audio/mpeg": {},
                "audio/wav": {},
                "audio/ogg": {},
            },
            "description": "The generated audio file.",
        }
    }
)
async def synthesize_speech(
    request: TextToSpeechRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    speech_service: Annotated[SpeechService, Depends(get_speech_service)],
) -> Response:
    """
    Generate speech from text. Returns binary audio.
    """
    result = await speech_service.synthesize_speech(
        text=request.text,
        voice=request.voice,
        user=user,
    )

    # Map common formats to their mime types
    media_types = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "opus": "audio/ogg",
        "aac": "audio/aac",
        "flac": "audio/flac",
    }

    media_type = media_types.get(result.audio_format, "application/octet-stream")

    return Response(content=result.audio_bytes, media_type=media_type)
