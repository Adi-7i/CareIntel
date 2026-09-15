"""
Consent API router.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from careintel.api.deps import CurrentUserDep, DbSessionDep, require_permission
from careintel.api.v1.consent.schemas import ConsentRequest, ConsentResponse
from careintel.application.auth.consent_service import ConsentService
from careintel.core.correlation import get_correlation_id
from careintel.domain.auth.permissions import Permission
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.consent_repo import ConsentRepository

router = APIRouter(prefix="/consent", tags=["consent"])


def get_consent_service(session: DbSessionDep) -> ConsentService:
    return ConsentService(
        consent_repo=ConsentRepository(session),
        audit_repo=AuditRepository(session),
    )


@router.post(
    "/request",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a consent request",
    dependencies=[require_permission(Permission.CONSENT_WRITE)],
)
async def request_consent(
    request: ConsentRequest,
    consent_service: Annotated[ConsentService, Depends(get_consent_service)],
) -> ConsentResponse:
    """Record that consent was requested from a user."""
    ctx = await consent_service.request_consent(
        subject_id=request.subject_id,
        purpose=request.purpose,
        notice_version=request.notice_version,
        correlation_id=get_correlation_id(),
    )
    return ConsentResponse.model_validate(ctx)


@router.post(
    "/{consent_id}/capture",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
    summary="Capture an accepted consent request",
    dependencies=[require_permission(Permission.CONSENT_WRITE)],
)
async def capture_consent(
    consent_id: uuid.UUID,
    current_user: CurrentUserDep,
    consent_service: Annotated[ConsentService, Depends(get_consent_service)],
) -> ConsentResponse:
    """Record that a requested consent was accepted."""
    ctx = await consent_service.capture_consent(
        consent_id=consent_id,
        actor=current_user,
        correlation_id=get_correlation_id(),
    )
    return ConsentResponse.model_validate(ctx)


@router.delete(
    "/{consent_id}",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
    summary="Withdraw an active consent",
    dependencies=[require_permission(Permission.CONSENT_WRITE)],
)
async def withdraw_consent(
    consent_id: uuid.UUID,
    current_user: CurrentUserDep,
    consent_service: Annotated[ConsentService, Depends(get_consent_service)],
) -> ConsentResponse:
    """Withdraw a previously granted consent."""
    ctx = await consent_service.withdraw_consent(
        consent_id=consent_id,
        actor=current_user,
        correlation_id=get_correlation_id(),
    )
    return ConsentResponse.model_validate(ctx)
