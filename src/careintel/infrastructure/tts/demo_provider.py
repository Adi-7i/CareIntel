"""
Demo Text-to-Speech Provider.
"""

from careintel.infrastructure.tts.port import TTSProvider, TTSResult


class DemoTTSProvider(TTSProvider):
    """
    Deterministic fake TTS provider for testing.
    """

    async def synthesize(self, text: str, voice: str | None = None) -> TTSResult:
        # A minimal valid WAV file header for 8kHz 8-bit mono
        # 44 bytes total
        fake_wav = (
            b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
            b"\x40\x1f\x00\x00\x40\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00"
        )
        
        return TTSResult(
            audio_bytes=fake_wav,
            audio_format="wav",
            provider="demo",
            model="demo-tts-v1",
            voice=voice or "demo-voice",
        )
