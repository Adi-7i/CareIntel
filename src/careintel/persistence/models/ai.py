"""
AI ORM models.

Tables:
- ai_runs          — Audit record for each AI task execution.
- ai_drafts        — Validated structured output awaiting reviewer decision.
- policy_decisions — Individual deterministic policy check results.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from careintel.persistence.base import Base


class AIRunORM(Base):
    """
    Audit record for a single AI task execution.

    Idempotency: UNIQUE(case_id, task_type, input_hash, prompt_version)
    prevents duplicate AI executions for identical inputs.
    """

    __tablename__ = "ai_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    schema_version: Mapped[str] = mapped_column(String, nullable=False)
    retrieval_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("retrieval_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    # IN_PROGRESS, COMPLETED, FAILED, REJECTED, POLICY_BLOCKED
    status: Mapped[str] = mapped_column(String, nullable=False, default="IN_PROGRESS")
    # SHA-256 of serialized SafeContext (for idempotency)
    input_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    # SHA-256 of raw AI response
    output_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Token usage: {'prompt_tokens': int, 'completion_tokens': int, 'total_tokens': int}
    usage_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    error_category: Mapped[str | None] = mapped_column(String, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    __table_args__ = (
        # Idempotency: same case+task+input+prompt version → existing run
        UniqueConstraint(
            "case_id",
            "task_type",
            "input_hash",
            "prompt_version",
            name="uq_ai_run_idempotency",
        ),
        Index("ix_ai_runs_case", "case_id"),
        Index("ix_ai_runs_status", "status"),
        Index("ix_ai_runs_actor", "actor_id"),
    )


class AIDraftORM(Base):
    """
    Validated AI-generated draft awaiting reviewer decision.

    One draft per AI run (1:1). A draft is NEVER clinically authoritative.
    Reviewer approval is required before any draft affects case state.
    """

    __tablename__ = "ai_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    ai_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    # Validated structured output as task-specific JSON
    content_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # ACCEPTED, REJECTED, REPAIR_ATTEMPTED
    validation_status: Mapped[str] = mapped_column(String, nullable=False)
    validation_errors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    # Claim → source provenance mappings
    provenance_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    # DRAFT, APPROVED, REJECTED (by human reviewer)
    reviewer_status: Mapped[str] = mapped_column(
        String, nullable=False, default="DRAFT"
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    __table_args__ = (Index("ix_ai_drafts_reviewer_status", "reviewer_status"),)


class PolicyDecisionORM(Base):
    """
    Record of a single deterministic policy check result.

    PolicyService runs independently from the LLM.
    Any FAIL outcome blocks the draft.
    """

    __tablename__ = "policy_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    ai_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    # PolicyCheckType enum value
    check_type: Mapped[str] = mapped_column(String, nullable=False)
    policy_version: Mapped[str] = mapped_column(String, nullable=False)
    # PASS, FAIL, WARN
    outcome: Mapped[str] = mapped_column(String, nullable=False)
    detail_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    __table_args__ = (Index("ix_policy_decisions_ai_run", "ai_run_id"),)
