"""
Escalation API endpoints.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

from careintel.api.deps import get_current_user
from careintel.core.errors import CapabilityNotImplementedError
from careintel.domain.auth.models import UserContext

router = APIRouter(tags=["escalation"])


@router.post("/cases/{case_id}/escalation", summary="Create escalation")
async def create_escalation(
    case_id: uuid.UUID,
    reason: Annotated[str, Body(embed=True)],
    expected_version: Annotated[int, Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError("Escalation API is not safely wired to persistence.")


@router.post("/escalations/{escalation_id}/resolve", summary="Resolve escalation")
async def resolve_escalation(
    escalation_id: uuid.UUID,
    resolution_notes: Annotated[str, Body(embed=True)],
    expected_case_version: Annotated[int, Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()
