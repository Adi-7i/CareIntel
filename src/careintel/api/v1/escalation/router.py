"""Human-controlled escalation endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from careintel.api.deps import get_current_user, get_escalation_service
from careintel.api.v1.escalation.schemas import (
    CreateEscalationRequest,
    EscalationResponse,
    ResolveEscalationRequest,
)
from careintel.application.escalation.escalation_service import EscalationService
from careintel.core.correlation import get_correlation_id
from careintel.domain.auth.models import UserContext

router = APIRouter(tags=["escalation"])


@router.post(
    "/cases/{case_id}/escalation",
    response_model=EscalationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_escalation(
    case_id: uuid.UUID,
    request: CreateEscalationRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationResponse:
    return EscalationResponse.model_validate(
        await service.create_escalation(
            case_id,
            request.reason,
            request.expected_case_version,
            request.expected_queue_version,
            actor,
            get_correlation_id(),
        )
    )


@router.post("/escalations/{escalation_id}/resolve", response_model=EscalationResponse)
async def resolve_escalation(
    escalation_id: uuid.UUID,
    request: ResolveEscalationRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationResponse:
    return EscalationResponse.model_validate(
        await service.resolve_escalation(
            escalation_id,
            request.resolution_notes,
            request.expected_case_version,
            request.expected_queue_version,
            actor,
            get_correlation_id(),
        )
    )
