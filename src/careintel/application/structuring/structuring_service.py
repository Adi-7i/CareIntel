"""
Structuring Engine orchestrator service.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.auth.consent_service import ConsentService
from careintel.application.structuring.checklist_loader import ChecklistLoader
from careintel.application.structuring.conflict_detector import (
    ConflictDetector,
    DemoCompatibilityPolicy,
)
from careintel.application.structuring.missing_info_evaluator import MissingInfoEvaluator
from careintel.application.structuring.temporal_normalizer import TemporalNormalizer
from careintel.core.config import Settings
from careintel.domain.audit.events import (
    CASE_STRUCTURED,
    STRUCTURING_FAILED,
    TIMELINE_EVALUATED,
)
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.evidence import EvidenceOutboxORM
from careintel.persistence.models.processing import ExtractedCandidateORM
from careintel.persistence.models.structuring import (
    ConflictCandidateLinkORM,
    ConflictRecordORM,
    StructuringRunORM,
    TimelineEventORM,
)
from careintel.persistence.repositories.structuring_repo import StructuringRepository


class StructuringService:
    """
    Orchestrates the end-to-end Case Structuring flow.
    """

    def __init__(
        self,
        session: AsyncSession,
        structuring_repo: StructuringRepository,
        consent_service: ConsentService,
        settings: Settings,
    ) -> None:
        self._session = session
        self._repo = structuring_repo
        self._consent_service = consent_service
        self._settings = settings

    async def evaluate_case(
        self,
        user: UserContext,
        case_id: uuid.UUID,
        extraction_run_id: uuid.UUID,
        candidates: list[ExtractedCandidateORM],
    ) -> uuid.UUID:
        """
        Execute the structuring pipeline for a case.
        Returns the StructuringRun ID.
        """
        # 1. Authorization
        if not AuthorizationPolicy.evaluate(user, Permission.STRUCTURING_WRITE, str(case_id)):
            from careintel.core.errors import AuthorizationError

            raise AuthorizationError("Not authorized to structure case.")

        # 2. Consent Check
        # Notice version should be fetched from active config/system, omitting for skeleton
        await self._consent_service.require_active(case_id, "structuring", "v1")

        # 3. Idempotency Check
        existing_run = await self._repo.get_run_by_idempotency_key(case_id, extraction_run_id)
        if existing_run:
            if existing_run.status in ("COMPLETED", "FAILED", "NO_INPUT"):
                return existing_run.id

        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        run_id = uuid.uuid4()

        # 4. Create Run
        run = StructuringRunORM(
            id=run_id,
            case_id=case_id,
            extraction_run_id=extraction_run_id,
            status="IN_PROGRESS",
            started_at=now,
        )
        await self._repo.create_run(run)

        try:
            if not candidates:
                await self._repo.update_run_status(run_id, status="NO_INPUT", completed_at=now)
                return run_id

            # 5. Load Policy
            policy = ChecklistLoader.load(
                self._settings.structuring_checklist_path,
                self._settings.structuring_active_checklist_version,
            )

            # 6. Timeline Construction (simplified)
            timeline_events: list[TimelineEventORM] = []
            for cand in candidates:
                temp_expr = TemporalNormalizer.normalize(cand.value)
                timeline_events.append(
                    TimelineEventORM(
                        id=uuid.uuid4(),
                        case_id=case_id,
                        structuring_run_id=run_id,
                        event_type=cand.field_type,
                        source_statement=cand.value,
                        raw_temporal_expression=temp_expr.raw_text,
                        temporal_precision=temp_expr.precision,
                        resolution_state=temp_expr.resolution_state,
                        normalized_start=temp_expr.normalized_start,
                        normalized_end=temp_expr.normalized_end,
                        anchor_description=temp_expr.anchor_description,
                        anchor_evidence_id=temp_expr.anchor_evidence_id,
                        unresolved_reason=temp_expr.unresolved_reason,
                        ordering_relation="UNKNOWN",
                        status="DRAFT",
                        evidence_id=cand.id,  # mock evidence mapping
                        candidate_id=cand.id,
                        extraction_run_id=extraction_run_id,
                        version=1,
                        created_at=now,
                    )
                )

            await self._repo.save_timeline_events(timeline_events)

            # 7. Conflict Detection
            conflict_domain_records = ConflictDetector.detect(
                case_id, run_id, candidates, DemoCompatibilityPolicy()
            )

            conflict_orms: list[ConflictRecordORM] = []
            conflict_links: list[ConflictCandidateLinkORM] = []
            for cr in conflict_domain_records:
                cr_orm = ConflictRecordORM(
                    id=cr.conflict_id,
                    case_id=cr.case_id,
                    field_type=cr.field_type,
                    status=cr.status,
                    detection_run_id=cr.detection_run_id,
                    created_at=now,
                    updated_at=now,
                )
                conflict_orms.append(cr_orm)
                for cid in cr.candidate_ids:
                    conflict_links.append(
                        ConflictCandidateLinkORM(
                            id=uuid.uuid4(),
                            conflict_id=cr.conflict_id,
                            candidate_id=cid,
                            created_at=now,
                            updated_at=now,
                        )
                    )
            await self._repo.save_conflict_records(conflict_orms, conflict_links)

            # 8. Missing Info Evaluation
            _ = MissingInfoEvaluator.evaluate(
                case_id, run_id, candidates, conflict_domain_records, policy
            )
            # ORM mapping omitted for missing items & questions in this skeleton service

            # 9. Outbox Events
            self._session.add(
                EvidenceOutboxORM(
                    id=uuid.uuid4(),
                    event_type=TIMELINE_EVALUATED,
                    payload={"case_id": str(case_id), "run_id": str(run_id)},
                )
            )
            self._session.add(
                EvidenceOutboxORM(
                    id=uuid.uuid4(),
                    event_type=CASE_STRUCTURED,
                    payload={"case_id": str(case_id), "run_id": str(run_id)},
                )
            )

            # 10. Audit
            self._session.add(
                AuditLogORM(
                    id=uuid.uuid4(),
                    actor_id=user.id,
                    event_type=CASE_STRUCTURED,
                    target_resource=str(case_id),
                    payload={"run_id": str(run_id)},
                )
            )

            await self._repo.update_run_status(run_id, status="COMPLETED", completed_at=now)
            return run_id

        except Exception as e:
            await self._repo.update_run_status(
                run_id, status="FAILED", failure_reason=str(e), completed_at=now
            )
            self._session.add(
                AuditLogORM(
                    id=uuid.uuid4(),
                    actor_id=user.id,
                    event_type=STRUCTURING_FAILED,
                    target_resource=str(case_id),
                    payload={"run_id": str(run_id), "error": str(e)},
                )
            )
            raise e
