"""
Review API endpoints.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

from careintel.api.deps import get_current_user
from careintel.core.errors import CapabilityNotImplementedError
from careintel.domain.auth.models import UserContext
from careintel.domain.review.states import ReviewDecisionType

# Normally we'd use Dependency Injection here to get the service,
# but for the sake of the plan implementation we'll mock the endpoint structures.

router = APIRouter(tags=["review"])


@router.get("/queue", summary="List review queue items")
async def list_queue(
    actor: Annotated[UserContext, Depends(get_current_user)],
    status: str | None = None,
    assigned_to: uuid.UUID | None = None,
) -> dict[str, Any]:
    raise CapabilityNotImplementedError("Reviewer queue API is not safely wired to persistence.")


@router.post("/queue/{case_id}/assign", summary="Assign reviewer")
async def assign_reviewer(
    case_id: uuid.UUID,
    reviewer_id: Annotated[uuid.UUID, Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/queue/{case_id}/reassign", summary="Reassign reviewer")
async def reassign_reviewer(
    case_id: uuid.UUID,
    new_reviewer_id: Annotated[uuid.UUID, Body(embed=True)],
    reason: Annotated[str, Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/cases/{case_id}/review/start", summary="Start review")
async def start_review(
    case_id: uuid.UUID,
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.get("/cases/{case_id}/review/workspace", summary="Get reviewer workspace")
async def get_reviewer_workspace(
    case_id: uuid.UUID,
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/cases/{case_id}/review/decision", summary="Submit review decision")
async def submit_decision(
    case_id: uuid.UUID,
    decision_type: Annotated[ReviewDecisionType, Body(embed=True)],
    expected_version: Annotated[int, Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
    rationale: Annotated[str | None, Body(embed=True)] = None,
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


# AI Draft Review Routes
@router.post("/drafts/{draft_id}/accept", summary="Accept AI draft")
async def accept_draft(
    draft_id: uuid.UUID,
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/drafts/{draft_id}/reject", summary="Reject AI draft")
async def reject_draft(
    draft_id: uuid.UUID,
    rationale: Annotated[str, Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()


@router.post("/drafts/{draft_id}/edit", summary="Edit AI draft")
async def edit_draft(
    draft_id: uuid.UUID,
    edited_content: Annotated[dict[str, Any], Body(embed=True)],
    actor: Annotated[UserContext, Depends(get_current_user)],
    rationale: Annotated[str | None, Body(embed=True)] = None,
) -> dict[str, Any]:
    raise CapabilityNotImplementedError()
