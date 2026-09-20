"""
Evidence router.
"""

import datetime
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from careintel.api.deps import (
    CurrentUserDep,
    get_evidence_service,
)
from careintel.api.v1.evidence.schemas import (
    EvidenceResponse,
    RegisterTextRequest,
    SecureDownloadResponse,
)
from careintel.application.evidence.evidence_service import EvidenceService
from careintel.core.config import get_settings
from careintel.core.correlation import get_correlation_id
from careintel.domain.evidence.commands import (
    RegisterTextEvidenceCommand,
    UploadFileEvidenceCommand,
)
from careintel.domain.evidence.modality import EvidenceModality

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post(
    "/text",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Text Evidence",
)
async def register_text(
    request: RegisterTextRequest,
    user: CurrentUserDep,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> EvidenceResponse:
    """Register raw text evidence directly."""
    cmd = RegisterTextEvidenceCommand(
        case_id=request.case_id,
        text_content=request.text_content,
        actor_id=user.id,
        correlation_id=correlation_id,
        consent_id=request.consent_id,
        encounter_id=request.encounter_id,
        source_language=request.source_language,
    )
    aggregate = await service.register_text_evidence(cmd, user)
    return EvidenceResponse.model_validate(aggregate)


@router.post(
    "/files",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload File Evidence",
)
async def upload_file(
    user: CurrentUserDep,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    case_id: Annotated[uuid.UUID, Form(...)],
    consent_id: Annotated[uuid.UUID, Form(...)],
    modality: Annotated[EvidenceModality, Form(...)],
    file: Annotated[UploadFile, File(...)],
    encounter_id: Annotated[uuid.UUID | None, Form()] = None,
) -> EvidenceResponse:
    """Upload a file as evidence."""
    cmd = UploadFileEvidenceCommand(
        case_id=case_id,
        modality=modality,
        declared_filename=file.filename or "unknown",
        declared_content_type=file.content_type or "application/octet-stream",
        actor_id=user.id,
        correlation_id=correlation_id,
        consent_id=consent_id,
        encounter_id=encounter_id,
    )

    # Start upload (creates PENDING_UPLOAD record)
    aggregate = await service.start_file_upload(cmd, user)

    # Stream and validate
    aggregate = await service.complete_file_upload(
        evidence_id=aggregate.evidence_id,
        file_stream=file.file,
        user=user,
        correlation_id=correlation_id,
    )
    return EvidenceResponse.model_validate(aggregate)


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Get Evidence Metadata",
)
async def get_evidence(
    evidence_id: uuid.UUID,
    user: CurrentUserDep,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
) -> EvidenceResponse:
    """Get metadata for a single evidence item."""
    aggregate = await service.get_evidence(evidence_id, user)
    return EvidenceResponse.model_validate(aggregate)


@router.get(
    "/{evidence_id}/download",
    response_model=SecureDownloadResponse,
    summary="Generate Secure Download URL",
)
async def download_evidence(
    evidence_id: uuid.UUID,
    user: CurrentUserDep,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> SecureDownloadResponse:
    """Generate a short-lived SAS URL for direct blob download."""
    url = await service.generate_secure_download_url(evidence_id, user, correlation_id)
    ttl = get_settings().evidence_sas_ttl_minutes
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=ttl)

    return SecureDownloadResponse(download_url=url, expires_at=expires_at)
