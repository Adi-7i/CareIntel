"""Authorized API boundary for persisted structuring results."""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from careintel.api.deps import CurrentUserDep
from careintel.api.v1.structuring.deps import StructuringServiceDep
from careintel.core.correlation import get_correlation_id

router = APIRouter(prefix="/cases", tags=["Structuring"])


class EvaluateRequest(BaseModel):
    extraction_run_id: uuid.UUID


class EvaluateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    status: str
    timeline_count: int
    conflict_count: int
    missing_info_count: int
    question_count: int


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    structuring_run_id: uuid.UUID
    event_type: str
    source_statement: str
    raw_temporal_expression: str
    temporal_precision: str
    resolution_state: str
    normalized_start: datetime.date | None
    normalized_end: datetime.date | None
    unresolved_reason: str | None
    status: str
    evidence_id: uuid.UUID
    candidate_id: uuid.UUID
    extraction_run_id: uuid.UUID


class ConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field_type: str
    status: str
    detection_run_id: uuid.UUID


class MissingInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evaluation_run_id: uuid.UUID
    requirement_key: str
    checklist_version: str
    status: str
    materiality: str
    resolution: str | None


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evaluation_run_id: uuid.UUID
    requirement_key: str
    missing_item_id: uuid.UUID
    question_text: str
    round_number: int
    status: str
    generator_version: str


class StructuringSummaryResponse(BaseModel):
    run_id: uuid.UUID
    extraction_run_id: uuid.UUID
    status: str
    timeline_count: int
    conflict_count: int
    missing_info_count: int
    question_count: int


@router.post("/{case_id}/evaluate", response_model=EvaluateResponse)
async def evaluate_case(
    case_id: uuid.UUID,
    request: EvaluateRequest,
    current_user: CurrentUserDep,
    service: StructuringServiceDep,
) -> EvaluateResponse:
    result = await service.evaluate_case(
        current_user,
        case_id,
        request.extraction_run_id,
        get_correlation_id(),
    )
    return EvaluateResponse.model_validate(result)


@router.get("/{case_id}/timeline", response_model=list[TimelineEventResponse])
async def get_timeline(
    case_id: uuid.UUID, current_user: CurrentUserDep, service: StructuringServiceDep
) -> list[TimelineEventResponse]:
    return [
        TimelineEventResponse.model_validate(item)
        for item in await service.get_timeline(case_id, current_user)
    ]


@router.get("/{case_id}/conflicts", response_model=list[ConflictResponse])
async def get_conflicts(
    case_id: uuid.UUID, current_user: CurrentUserDep, service: StructuringServiceDep
) -> list[ConflictResponse]:
    return [
        ConflictResponse.model_validate(item)
        for item in await service.get_conflicts(case_id, current_user)
    ]


@router.get("/{case_id}/missing-info", response_model=list[MissingInfoResponse])
async def get_missing_info(
    case_id: uuid.UUID, current_user: CurrentUserDep, service: StructuringServiceDep
) -> list[MissingInfoResponse]:
    return [
        MissingInfoResponse.model_validate(item)
        for item in await service.get_missing_info(case_id, current_user)
    ]


@router.get("/{case_id}/questions", response_model=list[QuestionResponse])
async def get_questions(
    case_id: uuid.UUID, current_user: CurrentUserDep, service: StructuringServiceDep
) -> list[QuestionResponse]:
    return [
        QuestionResponse.model_validate(item)
        for item in await service.get_questions(case_id, current_user)
    ]


@router.get("/{case_id}/summary", response_model=StructuringSummaryResponse)
async def get_summary(
    case_id: uuid.UUID, current_user: CurrentUserDep, service: StructuringServiceDep
) -> StructuringSummaryResponse:
    run, result = await service.get_summary(case_id, current_user)
    return StructuringSummaryResponse(
        run_id=run.id,
        extraction_run_id=run.extraction_run_id,
        status=result.status,
        timeline_count=result.timeline_count,
        conflict_count=result.conflict_count,
        missing_info_count=result.missing_info_count,
        question_count=result.question_count,
    )
