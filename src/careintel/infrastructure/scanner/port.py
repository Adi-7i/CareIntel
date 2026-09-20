"""
Scanner interface.
"""

import uuid
from enum import StrEnum
from typing import Protocol


class ScanResult(StrEnum):
    CLEAN = "CLEAN"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class ContentScannerPort(Protocol):
    """
    Interface for scanning files (e.g., malware, content rules).
    """

    async def scan(self, evidence_id: uuid.UUID, key: str) -> ScanResult:
        """Scan the specified object."""
        ...
