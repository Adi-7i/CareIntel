"""
OCR Provider interface.
"""

from typing import Protocol

from careintel.domain.processing.processing_models import OcrPage, OcrRegion


from dataclasses import dataclass, field

@dataclass(frozen=True)
class OcrTableData:
    """Structured table extracted from a document page."""
    page_number: int
    row_count: int
    column_count: int
    cells: list[dict[str, object]]  # [{row, col, text, is_header}, ...]
    markdown: str  # Markdown representation for LLM consumption

class OcrResult:
    """Standardized OCR output."""

    def __init__(
        self, pages: list[OcrPage], regions: list[OcrRegion], provider_version: str, tables: list[OcrTableData] | None = None
    ) -> None:
        self.pages = pages
        self.regions = regions
        self.provider_version = provider_version
        self.tables = tables or []


class OcrProvider(Protocol):
    """Protocol for OCR adapters."""

    async def process_document(self, file_path: str, run_id: str) -> OcrResult:
        """
        Process a document file and return standardized OCR output.
        Raises specific provider errors if processing fails.
        """
        ...
