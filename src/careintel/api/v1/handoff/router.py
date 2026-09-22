"""
Handoff API endpoints.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, Path

from careintel.api.deps import get_current_user
from careintel.domain.auth.models import UserContext

router = APIRouter(tags=["handoff"])


@router.post("/cases/{case_id}/referral", summary="Prepare referral package")
async def prepare_referral_package(
    case_id: uuid.UUID = Path(...),
    evidence_ids: list[uuid.UUID] = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "prepared"}


@router.post("/referrals/{package_id}/finalize", summary="Finalize package")
async def finalize_package(
    package_id: uuid.UUID = Path(...),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "finalized"}


@router.post("/referrals/{package_id}/handoff", summary="Initiate handoff")
async def initiate_handoff(
    package_id: uuid.UUID = Path(...),
    recipient_id: uuid.UUID = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "initiated"}


@router.post("/handoffs/{handoff_id}/send", summary="Send handoff")
async def send_handoff(
    handoff_id: uuid.UUID = Path(...),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "sending"}


@router.post("/handoffs/{handoff_id}/acknowledge", summary="Record acknowledgement")
async def record_acknowledgement(
    handoff_id: uuid.UUID = Path(...),
    reference: str = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "acknowledged"}


@router.post("/handoffs/{handoff_id}/complete", summary="Complete handoff")
async def complete_handoff(
    handoff_id: uuid.UUID = Path(...),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "completed"}


@router.get("/recipients", summary="List active recipients")
async def list_active_recipients(
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"recipients": []}
