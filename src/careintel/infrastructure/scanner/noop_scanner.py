"""
No-op content scanner.
"""

import uuid

from careintel.infrastructure.scanner.port import ContentScannerPort, ScanResult


class NoOpScanner(ContentScannerPort):
    """
    A scanner that always returns PENDING.
    Used in Phase 4 when no real scanner is wired.
    """

    async def scan(self, evidence_id: uuid.UUID, key: str) -> ScanResult:
        # Without a real scanner, evidence stops at STORED (PENDING scan)
        return ScanResult.PENDING
