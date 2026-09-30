"""Authenticated human-review endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from careintel.api.deps import (
    get_current_user,
    get_draft_review_service,
    get_review_decision_service,
    get_review_service,
    get_workspace_service,
)
from careintel.api.v1.review.schemas import (
    AssignReviewerRequest,
    DraftActionRequest,
    DraftActionResponse,
    EditDraftRequest,
    EnterQueueRequest,
    QueueItemResponse,
    ReassignReviewerRequest,
    RejectDraftRequest,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    VersionRequest,
)
from careintel.application.review.decision_service import ReviewDecisionService
from careintel.application.review.draft_service import DraftReviewService
from careintel.application.review.review_service import ReviewService
from careintel.application.review.workspace_service import WorkspaceService
from careintel.core.correlation import get_correlation_id
from careintel.domain.auth.models import UserContext

router = APIRouter(tags=["review"])


@router.get("/queue", response_model=list[QueueItemResponse])
async def list_queue(
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
    queue_status: str | None = Query(default=None, alias="status"),
    assigned_to: uuid.UUID | None = None,
) -> list[QueueItemResponse]:
    return [
        QueueItemResponse.model_validate(item)
        for item in await service.list_queue(actor, queue_status, assigned_to)
    ]


@router.post(
    "/cases/{case_id}/review/queue",
    response_model=QueueItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enter_queue(
    case_id: uuid.UUID,
    request: EnterQueueRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> QueueItemResponse:
    return QueueItemResponse.model_validate(
        await service.enter_review_queue(case_id, actor, get_correlation_id(), request.encounter_id)
    )


@router.post("/queue/{case_id}/assign", response_model=QueueItemResponse)
async def assign_reviewer(
    case_id: uuid.UUID,
    request: AssignReviewerRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> QueueItemResponse:
    return QueueItemResponse.model_validate(
        await service.assign_reviewer(
            case_id,
            request.reviewer_id,
            request.expected_version,
            actor,
            get_correlation_id(),
        )
    )


@router.post("/queue/{case_id}/reassign", response_model=QueueItemResponse)
async def reassign_reviewer(
    case_id: uuid.UUID,
    request: ReassignReviewerRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> QueueItemResponse:
    return QueueItemResponse.model_validate(
        await service.reassign_reviewer(
            case_id,
            request.reviewer_id,
            request.reason,
            request.expected_version,
            actor,
            get_correlation_id(),
        )
    )


@router.post("/cases/{case_id}/review/start", response_model=QueueItemResponse)
async def start_review(
    case_id: uuid.UUID,
    request: VersionRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> QueueItemResponse:
    return QueueItemResponse.model_validate(
        await service.start_review(case_id, request.expected_version, actor, get_correlation_id())
    )


@router.get("/cases/{case_id}/review/workspace")
async def get_reviewer_workspace(
    case_id: uuid.UUID,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> dict[str, Any]:
    return await service.get_reviewer_workspace(case_id, actor, get_correlation_id())


@router.post("/cases/{case_id}/review/decision", response_model=ReviewDecisionResponse)
async def submit_decision(
    case_id: uuid.UUID,
    request: ReviewDecisionRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[ReviewDecisionService, Depends(get_review_decision_service)],
) -> ReviewDecisionResponse:
    return ReviewDecisionResponse.model_validate(
        await service.submit_decision(
            case_id,
            request.draft_id,
            request.decision_type,
            request.rationale,
            request.expected_case_version,
            request.expected_queue_version,
            request.expected_draft_version,
            actor,
            get_correlation_id(),
        )
    )


def _draft_response(draft: Any) -> DraftActionResponse:
    return DraftActionResponse(
        id=draft.id,
        reviewer_status=draft.reviewer_status,
        reviewer_id=draft.reviewer_id,
        version=draft.version,
    )


@router.post("/drafts/{draft_id}/accept", response_model=DraftActionResponse)
async def accept_draft(
    draft_id: uuid.UUID,
    request: DraftActionRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[DraftReviewService, Depends(get_draft_review_service)],
) -> DraftActionResponse:
    return _draft_response(
        await service.accept_draft(
            draft_id,
            request.expected_draft_version,
            request.expected_queue_version,
            actor,
            get_correlation_id(),
        )
    )


@router.post("/drafts/{draft_id}/reject", response_model=DraftActionResponse)
async def reject_draft(
    draft_id: uuid.UUID,
    request: RejectDraftRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[DraftReviewService, Depends(get_draft_review_service)],
) -> DraftActionResponse:
    return _draft_response(
        await service.reject_draft(
            draft_id,
            request.rationale,
            request.expected_draft_version,
            request.expected_queue_version,
            actor,
            get_correlation_id(),
        )
    )


@router.post("/drafts/{draft_id}/edit", response_model=DraftActionResponse)
async def edit_draft(
    draft_id: uuid.UUID,
    request: EditDraftRequest,
    actor: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[DraftReviewService, Depends(get_draft_review_service)],
) -> DraftActionResponse:
    return _draft_response(
        await service.edit_draft(
            draft_id,
            request.edited_content,
            request.rationale,
            request.expected_draft_version,
            request.expected_queue_version,
            actor,
            get_correlation_id(),
        )
    )
