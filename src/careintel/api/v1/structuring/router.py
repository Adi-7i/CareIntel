"""
API Router for Structuring Engine.
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from careintel.api.deps import CurrentUserDep
from careintel.api.v1.structuring.deps import StructuringServiceDep
from careintel.core.errors import AuthorizationError, ConsentError
from careintel.persistence.models.processing import ExtractedCandidateORM

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
    try:
        # In a real implementation, we'd load candidates from ProcessingRepository.
        # For this skeleton, we pass an empty list, which results in a NO_INPUT run.
        candidates: list[ExtractedCandidateORM] = []

        run_id = await service.evaluate_case(
            current_user, case_id, request.extraction_run_id, candidates
        )
        return EvaluateResponse(run_id=run_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ConsentError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{case_id}/timeline")
async def get_timeline(case_id: uuid.UUID) -> Any:
    """Get timeline events (stub)."""
    return {"data": []}


@router.get("/{case_id}/conflicts")
async def get_conflicts(case_id: uuid.UUID) -> Any:
    """Get conflict records (stub)."""
    return {"data": []}


@router.get("/{case_id}/missing-info")
async def get_missing_info(case_id: uuid.UUID) -> Any:
    """Get missing info items (stub)."""
    return {"data": []}


@router.get("/{case_id}/questions")
async def get_questions(case_id: uuid.UUID) -> Any:
    """Get clarification questions (stub)."""
    return {"data": []}


@router.get("/{case_id}/summary")
async def get_summary(case_id: uuid.UUID) -> Any:
    """Get structured case summary (stub)."""
    return {"data": {}}
