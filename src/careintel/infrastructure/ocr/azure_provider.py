"""
Azure Document Intelligence OCR Provider.

Production OCR provider using azure-ai-documentintelligence.
Extracts pages, regions (paragraphs), and tables (when layout model is used).
"""

from __future__ import annotations

import asyncio
import uuid

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from careintel.domain.processing.processing_models import OcrPage, OcrRegion
from careintel.infrastructure.ocr.port import OcrProvider, OcrResult, OcrTableData


class AzureDocumentIntelligenceProvider(OcrProvider):
    """
    Azure Document Intelligence implementation of OcrProvider.
    """

    def __init__(self, endpoint: str, key: str, model: str = "prebuilt-layout") -> None:
        self._client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        self._model = model
        self._provider_version = f"azure-di-{model}-v1"

    async def process_document(self, file_path: str, run_id: str) -> OcrResult:
        """
        Process document asynchronously using a synchronous SDK call in a thread pool.
        """
        run_uuid = uuid.UUID(run_id)

        # Read file bytes
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Azure Document Intelligence call is synchronous, wrap it
        def _analyze() -> object:
            poller = self._client.begin_analyze_document(
                model_id=self._model,
                body=file_bytes,
                content_type="application/octet-stream"
            )
            return poller.result()

        result = await asyncio.to_thread(_analyze)

        pages = []
        regions = []
        tables = []

        # Map pages
        if hasattr(result, "pages") and result.pages:
            for p in result.pages:
                pages.append(
                    OcrPage(
                        page_id=uuid.uuid4(),
                        run_id=run_uuid,
                        page_number=p.page_number,
                        width=p.width,
                        height=p.height,
                        unit=p.unit,
                        confidence=None,  # DI doesn't provide page-level confidence directly here
                    )
                )

        # Map paragraphs/regions
        reading_order = 1
        page_id_map = {p.page_number: p.page_id for p in pages}

        if hasattr(result, "paragraphs") and result.paragraphs:
            for para in result.paragraphs:
                # Default to first page if spans are missing
                page_num = 1
                if para.bounding_regions and len(para.bounding_regions) > 0:
                    page_num = para.bounding_regions[0].page_number

                page_id = page_id_map.get(page_num, pages[0].page_id if pages else uuid.uuid4())

                bbox = None
                if para.bounding_regions and len(para.bounding_regions) > 0:
                    bbox = para.bounding_regions[0].polygon

                regions.append(
                    OcrRegion(
                        region_id=uuid.uuid4(),
                        page_id=page_id,
                        text=para.content,
                        reading_order=reading_order,
                        bounding_box=bbox,
                        confidence=None,
                    )
                )
                reading_order += 1

        # Map tables if using layout
        if hasattr(result, "tables") and result.tables:
            for tbl in result.tables:
                page_num = 1
                if tbl.bounding_regions and len(tbl.bounding_regions) > 0:
                    page_num = tbl.bounding_regions[0].page_number

                cells = []
                for cell in tbl.cells:
                    cells.append({
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "content": cell.content,
                        "kind": cell.kind if hasattr(cell, "kind") else "content",
                    })

                # Simple markdown table generation for LLM
                md_rows = []
                for r in range(tbl.row_count):
                    row_cells = [c for c in cells if c["row_index"] == r]
                    row_cells.sort(key=lambda x: x["column_index"])
                    row_text = "| " + " | ".join([c["content"].replace("\n", " ") for c in row_cells]) + " |"
                    md_rows.append(row_text)
                    if r == 0:
                        # Header separator
                        md_rows.append("|" + "|".join(["---" for _ in range(tbl.column_count)]) + "|")

                markdown = "\n".join(md_rows)

                tables.append(
                    OcrTableData(
                        page_number=page_num,
                        row_count=tbl.row_count,
                        column_count=tbl.column_count,
                        cells=cells,
                        markdown=markdown
                    )
                )

                # Add the table markdown as a region so it gets chunked/embedded
                page_id = page_id_map.get(page_num, pages[0].page_id if pages else uuid.uuid4())
                regions.append(
                    OcrRegion(
                        region_id=uuid.uuid4(),
                        page_id=page_id,
                        text=f"[TABLE]\n{markdown}",
                        reading_order=reading_order,
                        bounding_box=None,
                        confidence=None,
                    )
                )
                reading_order += 1

        # Fallback if no paragraphs but text exists (e.g. prebuilt-read)
        if not regions and hasattr(result, "content") and result.content:
            page_id = pages[0].page_id if pages else uuid.uuid4()
            regions.append(
                OcrRegion(
                    region_id=uuid.uuid4(),
                    page_id=page_id,
                    text=result.content,
                    reading_order=reading_order,
                    bounding_box=None,
                    confidence=None,
                )
            )

        return OcrResult(
            pages=pages,
            regions=regions,
            provider_version=self._provider_version,
            tables=tables,
        )
