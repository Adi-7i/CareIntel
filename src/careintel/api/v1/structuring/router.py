"""
API Router for Structuring Engine.
"""

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from careintel.api.deps import CurrentUserDep
from careintel.api.v1.structuring.deps import StructuringServiceDep
from careintel.core.errors import CapabilityNotImplementedError

router = APIRouter(prefix="/cases", tags=["Structuring"])


class EvaluateRequest(BaseModel):
    extraction_run_id: uuid.UUID


class EvaluateResponse(BaseModel):
    run_id: uuid.UUID


@router.post("/{case_id}/evaluate", response_model=EvaluateResponse)
async def evaluate_case(
    case_id: uuid.UUID,
    request: EvaluateRequest,
    current_user: CurrentUserDep,
    service: StructuringServiceDep,
) -> Any:
    """
    Trigger the synchronous structuring pipeline for a case.
    """
    raise CapabilityNotImplementedError(
        "Structuring is not safely wired to persisted extraction candidates."
    )


@router.get("/{case_id}/timeline")
async def get_timeline(case_id: uuid.UUID, _current_user: CurrentUserDep) -> Any:
    """Get timeline events (stub)."""
    raise CapabilityNotImplementedError()


@router.get("/{case_id}/conflicts")
async def get_conflicts(case_id: uuid.UUID, _current_user: CurrentUserDep) -> Any:
    """Get conflict records (stub)."""
    raise CapabilityNotImplementedError()


@router.get("/{case_id}/missing-info")
async def get_missing_info(case_id: uuid.UUID, _current_user: CurrentUserDep) -> Any:
    """Get missing info items (stub)."""
    raise CapabilityNotImplementedError()


@router.get("/{case_id}/questions")
async def get_questions(case_id: uuid.UUID, _current_user: CurrentUserDep) -> Any:
    """Get clarification questions (stub)."""
    raise CapabilityNotImplementedError()


@router.get("/{case_id}/summary")
async def get_summary(case_id: uuid.UUID, _current_user: CurrentUserDep) -> Any:
    """Get structured case summary (stub)."""
    raise CapabilityNotImplementedError()
