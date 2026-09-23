"""Case-scoped trusted-knowledge retrieval endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from careintel.api.deps import get_current_user, get_retrieval_service
from careintel.api.v1.retrieval.schemas import RetrievalRequest, RetrievalResponse
from careintel.application.retrieval.retrieval_service import RetrievalService
from careintel.domain.auth.models import UserContext

router = APIRouter(prefix="/cases/{case_id}/retrieval", tags=["retrieval"])


@router.post("", response_model=RetrievalResponse)
async def retrieve_knowledge(
    case_id: uuid.UUID,
    request: RetrievalRequest,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> RetrievalResponse:
    result = await service.retrieve_knowledge(
        current_user,
        case_id,
        request.query,
        request.corpus_version,
        request.search_mode,
        request.top_k,
    )
    return RetrievalResponse.model_validate(result)


@router.get("/{run_id}", response_model=RetrievalResponse)
async def get_retrieval_result(
    case_id: uuid.UUID,
    run_id: uuid.UUID,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> RetrievalResponse:
    return RetrievalResponse.model_validate(await service.get_result(current_user, case_id, run_id))
