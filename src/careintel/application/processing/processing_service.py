"""
Processing Orchestration Service.
"""

from __future__ import annotations

import logging
import uuid

from careintel.application.processing.document_processor import DocumentProcessor
from careintel.application.processing.extraction_processor import ExtractionProcessor
from careintel.application.processing.language_processor import LanguageProcessor
from careintel.application.processing.speech_processor import SpeechProcessor
from careintel.core.errors import CareIntelError
from careintel.domain.auth.models import UserContext
from careintel.domain.processing.processing_commands import TriggerProcessingCommand
from careintel.domain.processing.processor_type import ProcessorType


class ProcessingService:
    """Orchestrates different multimodal processing pipelines."""

    def __init__(
        self,
        document_processor: DocumentProcessor,
        speech_processor: SpeechProcessor,
        language_processor: LanguageProcessor,
        extraction_processor: ExtractionProcessor,
    ) -> None:
        self.document_processor = document_processor
        self.speech_processor = speech_processor
        self.language_processor = language_processor
        self.extraction_processor = extraction_processor
        self.logger = logging.getLogger(__name__)

    async def trigger_processing(
        self, command: TriggerProcessingCommand, user: UserContext, correlation_id: str
    ) -> uuid.UUID:
        """
        Triggers the appropriate processing pipeline based on ProcessorType.
        Returns the ProcessingRun ID.
        """
        self.logger.info(
            f"Triggering {command.processor_type} processing for evidence {command.evidence_id}"
        )

        if command.processor_type == ProcessorType.DOCUMENT_OCR.value:
            return await self.document_processor.process(command.evidence_id, user, correlation_id)

        elif command.processor_type == ProcessorType.SPEECH_TRANSCRIPTION.value:
            return await self.speech_processor.process(command.evidence_id, user, correlation_id)

        elif command.processor_type == ProcessorType.LANGUAGE_NORMALIZATION.value:
            # For Language and Extraction, they need input text.
            # Usually the command payload would provide this or it fetches it from previous run.
            # In Phase 5, we can assume the caller passes the text in command.parameters
            text = command.parameters.get("text", "")
            target_lang = command.parameters.get("target_language", "en")
            return await self.language_processor.process(
                command.evidence_id, text, user, correlation_id, target_language=target_lang
            )

        elif command.processor_type == ProcessorType.CANDIDATE_EXTRACTION.value:
            text = command.parameters.get("text", "")
            return await self.extraction_processor.process(
                command.evidence_id, text, user, correlation_id
            )

        else:
            raise CareIntelError(f"Unsupported processor type: {command.processor_type}")
