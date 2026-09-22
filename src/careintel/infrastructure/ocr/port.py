"""
OCR Provider interface.
"""

from typing import Protocol

from careintel.domain.processing.processing_models import OcrPage, OcrRegion


class OcrResult:
    """Standardized OCR output."""

    def __init__(
        self, pages: list[OcrPage], regions: list[OcrRegion], provider_version: str
    ) -> None:
        self.pages = pages
        self.regions = regions
        self.provider_version = provider_version


class OcrProvider(Protocol):
    """Protocol for OCR adapters."""

    async def process_document(self, file_path: str, run_id: str) -> OcrResult:
        """
        Process a document file and return standardized OCR output.
        Raises specific provider errors if processing fails.
        """
        ...
