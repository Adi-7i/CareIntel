"""
Processing API router.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from careintel.api.deps import get_current_user, get_processing_service
from careintel.api.v1.processing.schemas import (
    TriggerProcessingRequest,
    TriggerProcessingResponse,
)
from careintel.application.processing.processing_service import ProcessingService
from careintel.domain.auth.models import UserContext
from careintel.domain.processing.processing_commands import TriggerProcessingCommand
from careintel.domain.processing.processor_type import ProcessorType

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post(
    "/trigger",
    response_model=TriggerProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_processing(
    request: TriggerProcessingRequest,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    processing_service: Annotated[ProcessingService, Depends(get_processing_service)],
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> TriggerProcessingResponse:
    """
    Trigger a processing pipeline for a given evidence record.
    """
    correlation_id = x_correlation_id or "default-corr-id"

    command = TriggerProcessingCommand(
        evidence_id=request.evidence_id,
        processor_type=ProcessorType(request.processor_type),
        parameters=request.parameters,
    )

    run_id = await processing_service.trigger_processing(
        command=command,
        user=current_user,
        correlation_id=correlation_id,
    )

    return TriggerProcessingResponse(run_id=run_id)
