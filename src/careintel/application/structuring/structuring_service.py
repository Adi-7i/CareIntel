"""Persisted structuring, timeline, conflicts, missing information, and questions."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass

from ulid import ULID

from careintel.application.auth.consent_service import ConsentService
from careintel.application.auth.permission_service import PermissionService
from careintel.application.structuring.checklist_loader import ChecklistLoader
from careintel.application.structuring.conflict_detector import (
    ConflictDetector,
    DemoCompatibilityPolicy,
)
from careintel.application.structuring.missing_info_evaluator import MissingInfoEvaluator
from careintel.application.structuring.question_generator import TemplateQuestionGenerator
from careintel.application.structuring.temporal_normalizer import TemporalNormalizer
from careintel.core.config import Settings
from careintel.core.errors import NotFoundError, ValidationError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.domain.processing.processing_status import ProcessingStatus
from careintel.domain.structuring.questions import ClarificationQuestion
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM, CaseOutboxORM
from careintel.persistence.models.evidence import EvidenceORM
from careintel.persistence.models.processing import ExtractedCandidateORM
from careintel.persistence.models.structuring import (
    ClarificationQuestionORM,
    ConflictCandidateLinkORM,
    ConflictRecordORM,
    MissingInfoItemORM,
    StructuringRunORM,
    TimelineEventORM,
)
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository
from careintel.persistence.repositories.structuring_repo import StructuringRepository


@dataclass(frozen=True)
class StructuringResult:
    run_id: uuid.UUID
    status: str
    timeline_count: int
    conflict_count: int
    missing_info_count: int
    question_count: int


class StructuringService:
    """Executes structuring against one explicitly selected extraction run."""

    _TEMPORAL_FIELD_MARKERS = ("date", "time", "onset", "duration")

    def __init__(
        self,
        structuring_repo: StructuringRepository,
        processing_repo: ProcessingRepository,
        case_repo: CaseRepository,
        case_outbox_repo: CaseOutboxRepository,
        audit_repo: AuditRepository,
        consent_service: ConsentService,
        settings: Settings,
    ) -> None:
        self._repo = structuring_repo
        self._processing = processing_repo
        self._cases = case_repo
        self._outbox = case_outbox_repo
        self._audit = audit_repo
        self._consent = consent_service
        self._settings = settings

    async def _authorized_case(
        self, case_id: uuid.UUID, actor: UserContext, permission: Permission
    ) -> CaseORM:
        case = await self._cases.get_by_id(case_id)
        if case is None:
            raise NotFoundError("Case not found.")
        PermissionService.check(actor, permission, facility_scope=case.facility_id)
        return case

    async def _load_extraction_candidates(
        self, case_id: uuid.UUID, extraction_run_id: uuid.UUID
    ) -> list[ExtractedCandidateORM]:
        extraction = await self._processing.get_extraction_run(extraction_run_id)
        if extraction is None:
            raise NotFoundError("Extraction run not found.")
        processing = await self._processing.get_run_by_id(extraction.processing_run_id)
        if processing is None or processing.status != ProcessingStatus.COMPLETED.value:
            raise ValidationError("Extraction processing run is incomplete.")
        evidence = await self._processing.session.get(EvidenceORM, processing.evidence_id)
        if evidence is None or evidence.case_id != case_id:
            raise NotFoundError("Extraction run not found for case.")
        return await self._processing.get_candidates_for_extraction(extraction_run_id)

    @staticmethod
    def _candidate_evidence_id(candidate: ExtractedCandidateORM) -> uuid.UUID:
        for provenance in candidate.provenance_json:
            raw_id = provenance.get("evidence_id")
            if raw_id:
                try:
                    return uuid.UUID(str(raw_id))
                except ValueError:
                    break
        raise ValidationError("Extracted candidate has no valid evidence provenance.")

    async def evaluate_case(
        self,
        user: UserContext,
        case_id: uuid.UUID,
        extraction_run_id: uuid.UUID,
        correlation_id: str,
    ) -> StructuringResult:
        case = await self._authorized_case(case_id, user, Permission.STRUCTURING_WRITE)
        await self._consent.require_active(
            case.synthetic_subject_id,
            ConsentPurpose.DATA_PROCESSING.value,
            "1.0",
        )

        existing = await self._repo.get_run_by_idempotency_key(case_id, extraction_run_id)
        if existing is not None:
            return await self._result_for_run(existing)

        candidates = await self._load_extraction_candidates(case_id, extraction_run_id)
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        run = StructuringRunORM(
            id=uuid.uuid4(),
            case_id=case_id,
            extraction_run_id=extraction_run_id,
            status="IN_PROGRESS",
            started_at=now,
        )
        await self._repo.create_run(run)

        try:
            policy = ChecklistLoader.load(
                self._settings.structuring_checklist_path,
                self._settings.structuring_active_checklist_version,
            )

            timeline: list[TimelineEventORM] = []
            for candidate in candidates:
                if not any(
                    marker in candidate.field_type.lower()
                    for marker in self._TEMPORAL_FIELD_MARKERS
                ):
                    continue
                temporal = TemporalNormalizer.normalize(
                    candidate.normalized_value or candidate.value
                )
                evidence_id = self._candidate_evidence_id(candidate)
                timeline.append(
                    TimelineEventORM(
                        id=uuid.uuid4(),
                        case_id=case_id,
                        structuring_run_id=run.id,
                        event_type=candidate.field_type,
                        source_statement=candidate.value,
                        raw_temporal_expression=temporal.raw_text,
                        temporal_precision=temporal.precision.value,
                        resolution_state=temporal.resolution_state.value,
                        normalized_start=temporal.normalized_start,
                        normalized_end=temporal.normalized_end,
                        anchor_description=temporal.anchor_description,
                        anchor_evidence_id=temporal.anchor_evidence_id,
                        unresolved_reason=temporal.unresolved_reason,
                        ordering_relation="UNKNOWN",
                        ordering_confidence=None,
                        status="DRAFT",
                        evidence_id=evidence_id,
                        candidate_id=candidate.id,
                        extraction_run_id=extraction_run_id,
                        version=1,
                    )
                )
            await self._repo.save_timeline_events(timeline)

            conflicts = ConflictDetector.detect(
                case_id, run.id, candidates, DemoCompatibilityPolicy()
            )
            conflict_orms = [
                ConflictRecordORM(
                    id=conflict.conflict_id,
                    case_id=conflict.case_id,
                    field_type=conflict.field_type,
                    status=conflict.status.value,
                    detection_run_id=conflict.detection_run_id,
                )
                for conflict in conflicts
            ]
            conflict_links = [
                ConflictCandidateLinkORM(
                    id=uuid.uuid4(),
                    conflict_id=conflict.conflict_id,
                    candidate_id=candidate_id,
                )
                for conflict in conflicts
                for candidate_id in conflict.candidate_ids
            ]
            await self._repo.save_conflict_records(conflict_orms, conflict_links)

            missing = MissingInfoEvaluator.evaluate(case_id, run.id, candidates, conflicts, policy)
            missing_orms = [
                MissingInfoItemORM(
                    id=item.item_id,
                    case_id=item.case_id,
                    evaluation_run_id=item.evaluation_run_id,
                    requirement_key=item.requirement_key,
                    checklist_version=item.checklist_version,
                    status=item.status.value,
                    materiality=item.materiality,
                    resolution=item.resolution,
                )
                for item in missing
            ]
            await self._repo.save_missing_info_items(missing_orms)

            generator = TemplateQuestionGenerator()
            generated: list[ClarificationQuestion] = []
            for item in missing:
                if len(generated) >= policy.max_questions_per_round:
                    break
                question = generator.generate(item, policy, generated, round_number=1)
                if question is not None:
                    generated.append(question)
            await self._repo.save_questions(
                [
                    ClarificationQuestionORM(
                        id=question.question_id,
                        case_id=question.case_id,
                        evaluation_run_id=question.evaluation_run_id,
                        requirement_key=question.requirement_key,
                        missing_item_id=question.missing_item_id,
                        question_text=question.question_text,
                        round_number=question.round_number,
                        status=question.status.value,
                        generator_version=question.generator_version,
                    )
                    for question in generated
                ]
            )

            await self._repo.update_run_status(
                run.id,
                status="COMPLETED" if candidates else "NO_INPUT",
                completed_at=now,
            )
            run.status = "COMPLETED" if candidates else "NO_INPUT"
            run.completed_at = now

            await self._outbox.append(
                CaseOutboxORM(
                    id=str(ULID()),
                    event_type=AuditEventType.CASE_STRUCTURED.value,
                    event_version=1,
                    occurred_at=now,
                    producer="careintel.structuring",
                    correlation_id=correlation_id,
                    case_id=case_id,
                    actor_id=user.id,
                    aggregate_version=case.version,
                    payload={
                        "run_id": str(run.id),
                        "extraction_run_id": str(extraction_run_id),
                        "status": run.status,
                    },
                )
            )
            await self._audit.append(
                AuditLogORM(
                    event_type=AuditEventType.CASE_STRUCTURED.value,
                    actor_id=user.id,
                    target_id=case_id,
                    target_type="case",
                    correlation_id=correlation_id,
                    outcome="SUCCESS",
                    detail={
                        "run_id": str(run.id),
                        "timeline_count": len(timeline),
                        "conflict_count": len(conflicts),
                        "missing_info_count": len(missing),
                        "question_count": len(generated),
                    },
                )
            )
            return StructuringResult(
                run_id=run.id,
                status=run.status,
                timeline_count=len(timeline),
                conflict_count=len(conflicts),
                missing_info_count=len(missing),
                question_count=len(generated),
            )
        except Exception as exc:
            await self._repo.update_run_status(
                run.id,
                status="FAILED",
                failure_reason=type(exc).__name__,
                completed_at=now,
            )
            await self._audit.append(
                AuditLogORM(
                    event_type=AuditEventType.STRUCTURING_FAILED.value,
                    actor_id=user.id,
                    target_id=case_id,
                    target_type="case",
                    correlation_id=correlation_id,
                    outcome="FAILURE",
                    detail={"run_id": str(run.id), "error_type": type(exc).__name__},
                )
            )
            raise

    async def _result_for_run(self, run: StructuringRunORM) -> StructuringResult:
        timeline = await self._repo.get_timeline_events(run.case_id, run.id)
        conflicts = await self._repo.get_conflict_records(run.case_id, run.id)
        missing = await self._repo.get_missing_info_items(run.case_id, run.id)
        questions = await self._repo.get_clarification_questions(run.case_id, run.id)
        return StructuringResult(
            run_id=run.id,
            status=run.status,
            timeline_count=len(timeline),
            conflict_count=len(conflicts),
            missing_info_count=len(missing),
            question_count=len(questions),
        )

    async def get_latest_run(self, case_id: uuid.UUID, user: UserContext) -> StructuringRunORM:
        await self._authorized_case(case_id, user, Permission.STRUCTURING_READ)
        run = await self._repo.get_latest_successful_run(case_id)
        if run is None:
            raise NotFoundError("No completed structuring run exists for case.")
        return run

    async def get_timeline(self, case_id: uuid.UUID, user: UserContext) -> list[TimelineEventORM]:
        run = await self.get_latest_run(case_id, user)
        return await self._repo.get_timeline_events(case_id, run.id)

    async def get_conflicts(self, case_id: uuid.UUID, user: UserContext) -> list[ConflictRecordORM]:
        run = await self.get_latest_run(case_id, user)
        return await self._repo.get_conflict_records(case_id, run.id)

    async def get_missing_info(
        self, case_id: uuid.UUID, user: UserContext
    ) -> list[MissingInfoItemORM]:
        run = await self.get_latest_run(case_id, user)
        return await self._repo.get_missing_info_items(case_id, run.id)

    async def get_questions(
        self, case_id: uuid.UUID, user: UserContext
    ) -> list[ClarificationQuestionORM]:
        run = await self.get_latest_run(case_id, user)
        return await self._repo.get_clarification_questions(case_id, run.id)

    async def get_summary(
        self, case_id: uuid.UUID, user: UserContext
    ) -> tuple[StructuringRunORM, StructuringResult]:
        run = await self.get_latest_run(case_id, user)
        return run, await self._result_for_run(run)
