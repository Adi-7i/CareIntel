"""
Processing API router.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from careintel.api.deps import get_current_user, get_processing_service
from careintel.api.v1.processing.schemas import (
    ProcessingRunResponse,
    TriggerProcessingRequest,
    TriggerProcessingResponse,
)
from careintel.application.processing.processing_service import ProcessingService
from careintel.core.correlation import get_correlation_id
from careintel.domain.auth.models import UserContext
from careintel.domain.processing.processing_commands import TriggerProcessingCommand
from careintel.domain.processing.processor_type import ProcessorType

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post(
    "/execute",
    response_model=ProcessingRunResponse,
    status_code=status.HTTP_200_OK,
)
async def execute_processing(
    request: TriggerProcessingRequest,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    processing_service: Annotated[ProcessingService, Depends(get_processing_service)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> ProcessingRunResponse:
    """Execute a processing step and return its persisted terminal state."""
    record = await processing_service.execute_processing(
        TriggerProcessingCommand(
            evidence_id=request.evidence_id,
            processor_type=ProcessorType(request.processor_type),
            parameters=request.parameters,
        ),
        current_user,
        correlation_id,
    )
    return ProcessingRunResponse.model_validate(record)


@router.get("/runs/{run_id}", response_model=ProcessingRunResponse)
async def get_processing_run(
    run_id: uuid.UUID,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    processing_service: Annotated[ProcessingService, Depends(get_processing_service)],
) -> ProcessingRunResponse:
    """Read one persisted processing run after object authorization."""
    record = await processing_service.get_run(run_id, current_user)
    return ProcessingRunResponse.model_validate(record)


@router.post(
    "/trigger",
    response_model=TriggerProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_processing(
    request: TriggerProcessingRequest,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    processing_service: Annotated[ProcessingService, Depends(get_processing_service)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> TriggerProcessingResponse:
    """
    Trigger a processing pipeline for a given evidence record.
    """
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
