"""Retrieval request and response contracts."""

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from careintel.domain.retrieval.status import RetrievalStatus, SearchMode, SourceType


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    corpus_version: str = Field(min_length=1, max_length=100)
    search_mode: SearchMode = SearchMode.HYBRID
    top_k: int = Field(default=10, ge=1, le=50)


class RetrievalCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: uuid.UUID
    retrieval_run_id: uuid.UUID
    source_type: SourceType
    source_id: uuid.UUID
    rank: int
    dense_score: float | None
    sparse_score: float | None
    fusion_score: float | None
    citation_locator: str | None


class RetrievalMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    retrieval_run_id: uuid.UUID
    query_hash: str
    search_mode: SearchMode
    corpus_version: str | None
    embedding_version_key: str | None
    applied_filters: dict[str, str]
    candidate_count: int
    status: RetrievalStatus
    zero_result_reason: str | None
    created_at: datetime.datetime


class RetrievalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata: RetrievalMetadataResponse
    candidates: list[RetrievalCandidateResponse]
