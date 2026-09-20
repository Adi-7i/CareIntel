"""
Demo OCR Provider.
"""

import uuid

from careintel.domain.processing.processing_models import OcrPage, OcrRegion
from careintel.infrastructure.ocr.port import OcrProvider, OcrResult


class DemoOcrProvider(OcrProvider):
    """
    Deterministic fake OCR provider for testing.
    """

    async def process_document(self, file_path: str, run_id: str) -> OcrResult:
        run_uuid = uuid.UUID(run_id)

        # Fake one page with one region
        page_id = uuid.uuid4()
        page = OcrPage(
            page_id=page_id,
            run_id=run_uuid,
            page_number=1,
            width=800.0,
            height=600.0,
            unit="px",
            confidence=0.95,
        )

        region = OcrRegion(
            region_id=uuid.uuid4(),
            page_id=page_id,
            text="Demo Extracted Text from Document",
            reading_order=1,
            bounding_box=[10.0, 10.0, 790.0, 50.0],
            confidence=0.95,
        )

        return OcrResult(
            pages=[page],
            regions=[region],
            provider_version="demo-ocr-v1",
        )
