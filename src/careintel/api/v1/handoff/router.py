"""Consent-gated referral, delivery, and acknowledgement endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from careintel.api.deps import (
    get_current_user,
    get_handoff_service,
    get_recipient_service,
    get_referral_service,
)
from careintel.api.v1.handoff.schemas import (
    AcknowledgeHandoffRequest,
    CompleteHandoffRequest,
    HandoffResponse,
    InitiateHandoffRequest,
    PrepareReferralRequest,
    RecipientResponse,
    ReferralPackageResponse,
    SendHandoffRequest,
)
from careintel.application.handoff.handoff_service import HandoffService
from careintel.application.handoff.recipient_service import RecipientService
from careintel.application.handoff.referral_service import ReferralPackageService
from careintel.core.correlation import get_correlation_id
from careintel.domain.auth.models import UserContext

router = APIRouter(tags=["handoff"])


@router.post(
    "/cases/{case_id}/referral",
    response_model=ReferralPackageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def prepare_referral_package(
    case_id: uuid.UUID,
    request: PrepareReferralRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[ReferralPackageService, Depends(get_referral_service)],
) -> ReferralPackageResponse:
    return ReferralPackageResponse.model_validate(
        await service.prepare_referral_package(
            case_id, request.evidence_ids, actor, get_correlation_id()
        )
    )


@router.post("/referrals/{package_id}/finalize", response_model=ReferralPackageResponse)
async def finalize_package(
    package_id: uuid.UUID,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[ReferralPackageService, Depends(get_referral_service)],
) -> ReferralPackageResponse:
    return ReferralPackageResponse.model_validate(
        await service.finalize_package(package_id, actor, get_correlation_id())
    )


@router.post(
    "/referrals/{package_id}/handoff",
    response_model=HandoffResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_handoff(
    package_id: uuid.UUID,
    request: InitiateHandoffRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[HandoffService, Depends(get_handoff_service)],
) -> HandoffResponse:
    return HandoffResponse.model_validate(
        await service.initiate_handoff(
            package_id, request.recipient_id, actor, get_correlation_id()
        )
    )


@router.post("/handoffs/{handoff_id}/send", response_model=HandoffResponse)
async def send_handoff(
    handoff_id: uuid.UUID,
    request: SendHandoffRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[HandoffService, Depends(get_handoff_service)],
) -> HandoffResponse:
    return HandoffResponse.model_validate(
        await service.send_handoff(
            handoff_id, request.expected_version, actor, get_correlation_id()
        )
    )


@router.post("/handoffs/{handoff_id}/acknowledge", response_model=HandoffResponse)
async def record_acknowledgement(
    handoff_id: uuid.UUID,
    request: AcknowledgeHandoffRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[HandoffService, Depends(get_handoff_service)],
) -> HandoffResponse:
    return HandoffResponse.model_validate(
        await service.record_acknowledgement(
            handoff_id,
            request.reference,
            request.expected_version,
            actor,
            get_correlation_id(),
        )
    )


@router.post("/handoffs/{handoff_id}/complete", response_model=HandoffResponse)
async def complete_handoff(
    handoff_id: uuid.UUID,
    request: CompleteHandoffRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[HandoffService, Depends(get_handoff_service)],
) -> HandoffResponse:
    return HandoffResponse.model_validate(
        await service.complete_handoff(
            handoff_id,
            request.expected_handoff_version,
            request.expected_case_version,
            actor,
            get_correlation_id(),
        )
    )


@router.get("/recipients", response_model=list[RecipientResponse])
async def list_active_recipients(
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[RecipientService, Depends(get_recipient_service)],
) -> list[RecipientResponse]:
    return [
        RecipientResponse.model_validate(item)
        for item in await service.list_active_recipients(actor)
    ]
