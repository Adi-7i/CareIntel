"""
Review API endpoints.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, Path

from careintel.api.deps import get_current_user
from careintel.domain.auth.models import UserContext
from careintel.domain.review.states import ReviewDecisionType

# Normally we'd use Dependency Injection here to get the service,
# but for the sake of the plan implementation we'll mock the endpoint structures.

router = APIRouter(tags=["review"])


@router.get("/queue", summary="List review queue items")
async def list_queue(
    status: str | None = None,
    assigned_to: uuid.UUID | None = None,
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"items": []}


@router.post("/queue/{case_id}/assign", summary="Assign reviewer")
async def assign_reviewer(
    case_id: uuid.UUID = Path(...),
    reviewer_id: uuid.UUID = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "assigned"}


@router.post("/queue/{case_id}/reassign", summary="Reassign reviewer")
async def reassign_reviewer(
    case_id: uuid.UUID = Path(...),
    new_reviewer_id: uuid.UUID = Body(..., embed=True),
    reason: str = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "reassigned"}


@router.post("/cases/{case_id}/review/start", summary="Start review")
async def start_review(
    case_id: uuid.UUID = Path(...),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "in_review"}


@router.get("/cases/{case_id}/review/workspace", summary="Get reviewer workspace")
async def get_reviewer_workspace(
    case_id: uuid.UUID = Path(...),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"case": {"id": str(case_id)}}


@router.post("/cases/{case_id}/review/decision", summary="Submit review decision")
async def submit_decision(
    case_id: uuid.UUID = Path(...),
    decision_type: ReviewDecisionType = Body(..., embed=True),
    rationale: str | None = Body(None, embed=True),
    expected_version: int = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "decision_submitted"}


# AI Draft Review Routes
@router.post("/drafts/{draft_id}/accept", summary="Accept AI draft")
async def accept_draft(
    draft_id: uuid.UUID = Path(...),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "accepted"}


@router.post("/drafts/{draft_id}/reject", summary="Reject AI draft")
async def reject_draft(
    draft_id: uuid.UUID = Path(...),
    rationale: str = Body(..., embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "rejected"}


@router.post("/drafts/{draft_id}/edit", summary="Edit AI draft")
async def edit_draft(
    draft_id: uuid.UUID = Path(...),
    edited_content: dict = Body(..., embed=True),
    rationale: str | None = Body(None, embed=True),
    actor: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    return {"status": "edited"}
