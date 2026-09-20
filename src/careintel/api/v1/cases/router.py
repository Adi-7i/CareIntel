"""
Case API router.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from careintel.api.deps import CurrentUserDep, DbSessionDep, get_case_service, require_permission
from careintel.api.v1.cases.schemas import (
    CaseHistoryResponse,
    CaseResponse,
    CaseStateHistoryEntry,
    CreateCaseRequest,
    TransitionRequest,
)
from careintel.application.case.case_service import CaseService
from careintel.core.correlation import get_correlation_id
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.commands import CreateCaseCommand, TransitionCaseCommand
from careintel.domain.consent.models import ConsentContext
from careintel.domain.consent.policy import ConsentPolicy
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.persistence.repositories.consent_repo import ConsentRepository

router = APIRouter(prefix="/cases", tags=["cases"])


CaseServiceDep = Annotated[CaseService, Depends(get_case_service)]


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_permission(Permission.CASE_WRITE)],
)
async def create_case(
    request: CreateCaseRequest,
    case_service: CaseServiceDep,
    user: CurrentUserDep,
    session: DbSessionDep,
) -> CaseResponse:
    """
    Create a new case.
    Requires an active consent for Data Processing.
    """
    # 1. Verify consent
    consent_repo = ConsentRepository(session)
    consent_orm = await consent_repo.get_by_id(request.consent_id)

    consent_ctx = None
    if consent_orm:
        consent_ctx = ConsentContext(
            id=consent_orm.id,
            subject_id=consent_orm.subject_id,
            purpose=consent_orm.purpose,
            notice_version=consent_orm.notice_version,
            state=consent_orm.state,
        )

    # Throws ConsentError if invalid
    ConsentPolicy.require_active(
        consent=consent_ctx,
        subject_id=request.synthetic_subject_id,
        purpose=ConsentPurpose.DATA_PROCESSING,
        required_notice_version="1.0",
    )

    # 2. Command
    cmd = CreateCaseCommand(
        synthetic_subject_id=request.synthetic_subject_id,
        facility_id=request.facility_id,
        opened_by=user.id,
        correlation_id=get_correlation_id(),
    )

    # 3. Execute
    aggregate = await case_service.create_case(cmd, user)
    return CaseResponse.model_validate(aggregate, from_attributes=True)


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    dependencies=[require_permission(Permission.CASE_READ)],
)
async def get_case(
    case_id: uuid.UUID,
    case_service: CaseServiceDep,
    user: CurrentUserDep,
) -> CaseResponse:
    """Get a case by ID."""
    aggregate = await case_service.get_case(case_id, user)
    return CaseResponse.model_validate(aggregate, from_attributes=True)


@router.post(
    "/{case_id}/transitions",
    response_model=CaseResponse,
    dependencies=[require_permission(Permission.CASE_WRITE)],
)
async def transition_case(
    case_id: uuid.UUID,
    request: TransitionRequest,
    case_service: CaseServiceDep,
    user: CurrentUserDep,
) -> CaseResponse:
    """
    Transition case to a new state using optimistic concurrency.
    """
    # Provide a placeholder from_state (it will be loaded and validated by the service)
    cmd = TransitionCaseCommand(
        case_id=case_id,
        actor_id=user.id,
        from_state="UNKNOWN",  # Will be replaced with actual state during processing
        to_state=request.to_state,
        expected_version=request.expected_version,
        reason=request.reason,
        correlation_id=get_correlation_id(),
    )

    aggregate = await case_service.transition_state(cmd, user)
    return CaseResponse.model_validate(aggregate, from_attributes=True)


@router.get(
    "/{case_id}/history",
    response_model=CaseHistoryResponse,
    dependencies=[require_permission(Permission.CASE_READ)],
)
async def get_case_history(
    case_id: uuid.UUID,
    case_service: CaseServiceDep,
    user: CurrentUserDep,
) -> CaseHistoryResponse:
    """Get the state transition history for a case."""
    history = await case_service.get_state_history(case_id, user)
    entries = [CaseStateHistoryEntry.model_validate(h) for h in history]
    return CaseHistoryResponse(case_id=case_id, history=entries)
