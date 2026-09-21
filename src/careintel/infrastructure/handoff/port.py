"""
Handoff Provider Port.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class DeliveryResult:
    """Result of a handoff delivery attempt."""

    success: bool
    reference: str | None = None
    failure_reason: str | None = None


class HandoffProvider(Protocol):
    """
    Protocol for handoff delivery providers.
    
    Implementing classes could send FHIR, HL7, email, secure messaging, etc.
    """

    async def deliver(self, package_content: dict[str, Any], recipient_config: dict[str, Any]) -> DeliveryResult:
        """
        Attempts to deliver the package content using the provided recipient configuration.
        """
        ...
