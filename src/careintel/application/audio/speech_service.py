"""
Speech Service (TTS Application Layer).

Orchestrates the conversion of text to speech while enforcing limits,
authorization, and auditing.
"""

from __future__ import annotations

import logging
import uuid

from careintel.core.correlation import get_correlation_id
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.infrastructure.tts.port import TTSProvider, TTSResult
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.repositories.audit_repo import AuditRepository


class SpeechService:
    """Application service for Text-to-Speech synthesis."""

    # Maximum length for a single TTS request to prevent abuse
    MAX_TEXT_LENGTH = 4096

    def __init__(
        self,
        tts_provider: TTSProvider,
        audit_repo: AuditRepository,
    ) -> None:
        self.tts_provider = tts_provider
        self.audit_repo = audit_repo
        self.logger = logging.getLogger(__name__)

    async def synthesize_speech(
        self,
        text: str,
        voice: str | None,
        user: UserContext,
    ) -> TTSResult:
        """
        Synthesizes speech from text.

        Enforces text length limits and audits the request.
        """
        if len(text) > self.MAX_TEXT_LENGTH:
            from careintel.core.errors import ValidationError

            raise ValidationError(
                message=f"Text length exceeds maximum allowed ({self.MAX_TEXT_LENGTH} chars)"
            )

        if not text.strip():
            from careintel.core.errors import ValidationError

            raise ValidationError(message="Text cannot be empty")

        self.logger.info(
            "Synthesizing speech",
            extra={"text_length": len(text), "voice": voice},
        )

        try:
            result = await self.tts_provider.synthesize(text=text, voice=voice)

            # Audit success
            await self._audit_event(
                event_type=AuditEventType.PROCESSING_COMPLETED,
                actor_id=user.id,
                target_id=None,
                target_type="tts",
                outcome="SUCCESS",
                detail={
                    "text_length": len(text),
                    "provider": result.provider,
                    "voice": result.voice,
                },
            )

            return result

        except Exception as exc:
            # Audit failure
            await self._audit_event(
                event_type=AuditEventType.PROCESSING_FAILED,
                actor_id=user.id,
                target_id=None,
                target_type="tts",
                outcome="FAILED",
                detail={
                    "text_length": len(text),
                    "error_type": type(exc).__name__,
                },
            )
            self.logger.error(
                "TTS synthesis failed",
                extra={"error_type": type(exc).__name__},
            )
            raise

    async def _audit_event(
        self,
        event_type: AuditEventType,
        actor_id: uuid.UUID,
        target_id: uuid.UUID | None,
        target_type: str | None,
        outcome: str,
        detail: dict[str, object] | None = None,
    ) -> None:
        entry = AuditLogORM(
            event_type=event_type.value,
            actor_id=actor_id,
            target_id=target_id,
            target_type=target_type,
            correlation_id=get_correlation_id(),
            outcome=outcome,
            detail=detail,
        )
        await self.audit_repo.append(entry)
