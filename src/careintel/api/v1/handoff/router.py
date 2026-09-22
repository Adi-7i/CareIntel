"""
Handoff API endpoints.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

from careintel.api.deps import get_current_user
from careintel.core.errors import CapabilityNotImplementedError
from careintel.domain.auth.models import UserContext

router = APIRouter(tags=["handoff"])


@router.post("/cases/{case_id}/referral", summary="Prepare referral package")
async def prepare_referral_package(
    case_id: uuid.UUID,
    evidence_ids: Annotated[list[uuid.UUID], Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError("Referral API is not safely wired to persistence.")


@router.post("/referrals/{package_id}/finalize", summary="Finalize package")
async def finalize_package(
    package_id: uuid.UUID,
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/referrals/{package_id}/handoff", summary="Initiate handoff")
async def initiate_handoff(
    package_id: uuid.UUID,
    recipient_id: Annotated[uuid.UUID, Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/handoffs/{handoff_id}/send", summary="Send handoff")
async def send_handoff(
    handoff_id: uuid.UUID,
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/handoffs/{handoff_id}/acknowledge", summary="Record acknowledgement")
async def record_acknowledgement(
    handoff_id: uuid.UUID,
    reference: Annotated[str, Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/handoffs/{handoff_id}/complete", summary="Complete handoff")
async def complete_handoff(
    handoff_id: uuid.UUID,
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.get("/recipients", summary="List active recipients")
async def list_active_recipients(
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()
