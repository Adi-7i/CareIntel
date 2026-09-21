"""
Escalation API endpoints.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, Path

from careintel.api.deps import get_current_user
from careintel.domain.auth.models import UserContext

router = APIRouter(tags=["escalation"])


@router.post("/cases/{case_id}/escalation", summary="Create escalation")
async def create_escalation(
    case_id: uuid.UUID = Path(...),
    reason: str = Body(..., embed=True),
    expected_version: int = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "escalated"}


@router.post("/escalations/{escalation_id}/resolve", summary="Resolve escalation")
async def resolve_escalation(
    escalation_id: uuid.UUID = Path(...),
    resolution_notes: str = Body(..., embed=True),
    expected_case_version: int = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "resolved"}
