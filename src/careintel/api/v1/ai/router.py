"""Human-review-bound advisory AI endpoint."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from careintel.api.deps import get_ai_workflow_service, get_current_user
from careintel.api.v1.ai.schemas import AIDraftResponse, ExecuteAdvisoryRequest
from careintel.application.ai.ai_workflow_service import AIWorkflowService
from careintel.domain.auth.models import UserContext

router = APIRouter(prefix="/cases/{case_id}/ai", tags=["ai"])


@router.post("/drafts", response_model=AIDraftResponse)
async def execute_advisory(
    case_id: uuid.UUID,
    request: ExecuteAdvisoryRequest,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[AIWorkflowService, Depends(get_ai_workflow_service)],
) -> AIDraftResponse:
    draft = await service.execute_advisory(
        current_user,
        case_id,
        request.retrieval_run_id,
        request.task_type,
    )
    return AIDraftResponse.model_validate(draft)
