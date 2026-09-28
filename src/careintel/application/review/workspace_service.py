"""Authorized reviewer workspace with explicit source/derived/AI separation."""

from __future__ import annotations

import uuid
from typing import Any

from careintel.application.auth.consent_service import ConsentService
from careintel.application.review.access import ReviewAccessGuard
from careintel.core.errors import NotFoundError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.repositories.ai_repo import AIRepository
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.encounter_repo import EncounterRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.handoff_repo import HandoffRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository
from careintel.persistence.repositories.retrieval_repo import RetrievalRepository
from careintel.persistence.repositories.review_repo import ReviewRepository
from careintel.persistence.repositories.structuring_repo import StructuringRepository
from careintel.persistence.repositories.text_content_repo import TextContentRepository


class WorkspaceService:
    def __init__(
        self,
        case_repo: CaseRepository,
        review_repo: ReviewRepository,
        encounter_repo: EncounterRepository,
        evidence_repo: EvidenceRepository,
        text_repo: TextContentRepository,
        processing_repo: ProcessingRepository,
        structuring_repo: StructuringRepository,
        retrieval_repo: RetrievalRepository,
        ai_repo: AIRepository,
        handoff_repo: HandoffRepository,
        consent_service: ConsentService,
        audit_repo: AuditRepository,
    ) -> None:
        self.case_repo = case_repo
        self.review_repo = review_repo
        self.encounter_repo = encounter_repo
        self.evidence_repo = evidence_repo
        self.text_repo = text_repo
        self.processing_repo = processing_repo
        self.structuring_repo = structuring_repo
        self.retrieval_repo = retrieval_repo
        self.ai_repo = ai_repo
        self.handoff_repo = handoff_repo
        self.audit_repo = audit_repo
        self.access = ReviewAccessGuard(case_repo, consent_service)

    async def get_reviewer_workspace(
        self, case_id: uuid.UUID, actor: UserContext, correlation_id: str
    ) -> dict[str, Any]:
        case = await self.access.require_case(case_id, actor, Permission.REVIEW_READ)
        queue = await self.review_repo.get_queue_item(case_id)
        if queue is None:
            raise NotFoundError("Review queue item not found.")
        self.access.require_assigned(queue, actor)

        encounters = await self.encounter_repo.list_for_case(case_id)
        evidence_items = list(await self.evidence_repo.get_by_case_id(case_id))
        original_evidence: list[dict[str, Any]] = []
        processing: list[dict[str, Any]] = []
        for evidence in evidence_items:
            text = await self.text_repo.get_for_evidence(evidence.id)
            original_evidence.append(
                {
                    "origin": "ORIGINAL_EVIDENCE",
                    "id": str(evidence.id),
                    "encounter_id": str(evidence.encounter_id) if evidence.encounter_id else None,
                    "modality": evidence.modality,
                    "state": evidence.state,
                    "filename": evidence.original_filename,
                    "content_type": evidence.content_type,
                    "text_content": text.content if text is not None else None,
                    "source_route": f"/api/v1/evidence/{evidence.id}/download",
                }
            )
            for run in await self.processing_repo.list_runs_for_evidence(evidence.id):
                item: dict[str, Any] = {
                    "origin": "DERIVED_ARTIFACT",
                    "run_id": str(run.id),
                    "evidence_id": str(evidence.id),
                    "processor_type": run.processor_type,
                    "provider": run.provider,
                    "status": run.status,
                    "failure_reason": run.failure_reason,
                }
                pages = await self.processing_repo.get_ocr_pages_for_run(run.id)
                item["ocr_regions"] = [
                    {
                        "page_number": page.page_number,
                        "region_id": str(region.id),
                        "text": region.text_content,
                        "bounding_box": region.bounding_box,
                    }
                    for page in pages
                    for region in await self.processing_repo.get_ocr_regions_for_page(page.id)
                ]
                item["transcript_segments"] = [
                    {
                        "segment_id": str(segment.id),
                        "start_time_ms": segment.start_time_ms,
                        "end_time_ms": segment.end_time_ms,
                        "text": segment.text_content,
                        "speaker_label": segment.speaker_label,
                    }
                    for segment in await self.processing_repo.get_transcript_segments_for_run(
                        run.id
                    )
                ]
                extraction = await self.processing_repo.get_extraction_run_for_processing(run.id)
                item["extracted_candidates"] = (
                    [
                        {
                            "candidate_id": str(candidate.id),
                            "field_type": candidate.field_type,
                            "value": candidate.value,
                            "status": candidate.status,
                            "provenance": candidate.provenance_json,
                        }
                        for candidate in await self.processing_repo.get_candidates_for_extraction(
                            extraction.id
                        )
                    ]
                    if extraction is not None
                    else []
                )
                processing.append(item)

        structuring_run = await self.structuring_repo.get_latest_successful_run(case_id)
        timeline: list[Any] = []
        missing: list[Any] = []
        conflicts: list[Any] = []
        questions: list[Any] = []
        if structuring_run is not None:
            timeline = await self.structuring_repo.get_timeline_events(case_id, structuring_run.id)
            missing = await self.structuring_repo.get_missing_info_items(
                case_id, structuring_run.id
            )
            conflicts = await self.structuring_repo.get_conflict_records(
                case_id, structuring_run.id
            )
            questions = await self.structuring_repo.get_clarification_questions(
                case_id, structuring_run.id
            )

        retrieval = []
        for retrieval_run in await self.retrieval_repo.list_runs_for_case(case_id):
            candidates = await self.retrieval_repo.get_candidates_for_run(retrieval_run.id)
            retrieval.append(
                {
                    "run_id": str(retrieval_run.id),
                    "status": retrieval_run.status,
                    "corpus_version": retrieval_run.corpus_version,
                    "candidates": [
                        {
                            "source_id": str(candidate.source_id),
                            "rank": candidate.rank,
                            "citation": candidate.citation_locator,
                        }
                        for candidate in candidates
                    ],
                }
            )

        drafts = await self.ai_repo.list_drafts_for_case(case_id)
        policy_decisions = await self.ai_repo.get_policy_decisions_for_case(case_id)
        decisions = await self.review_repo.get_decisions_for_case(case_id)
        note = await self.review_repo.get_active_note_for_case(case_id)
        escalations = await self.review_repo.get_escalations_for_case(case_id)
        packages = await self.handoff_repo.get_packages_for_case(case_id)
        handoffs = await self.handoff_repo.get_handoffs_for_case(case_id)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.REVIEW_WORKSPACE_ACCESSED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )
        return {
            "case": {
                "id": str(case.id),
                "state": case.state,
                "version": case.version,
                "assigned_to": str(case.assigned_to) if case.assigned_to else None,
            },
            "queue_item": {
                "id": str(queue.id),
                "status": queue.status,
                "version": queue.version,
                "assigned_reviewer_id": (
                    str(queue.assigned_reviewer_id) if queue.assigned_reviewer_id else None
                ),
            },
            "encounters": [
                {
                    "id": str(encounter.id),
                    "type": encounter.encounter_type,
                    "occurred_at": encounter.occurred_at.isoformat(),
                }
                for encounter in encounters
            ],
            "original_evidence": original_evidence,
            "derived_information": {
                "processing": processing,
                "timeline": [
                    {
                        "id": str(item.id),
                        "source_statement": item.source_statement,
                        "temporal_expression": item.raw_temporal_expression,
                        "resolution_state": item.resolution_state,
                        "evidence_id": str(item.evidence_id),
                    }
                    for item in timeline
                ],
                "missing_information": [
                    {
                        "id": str(item.id),
                        "requirement_key": item.requirement_key,
                        "status": item.status,
                    }
                    for item in missing
                ],
                "conflicts": [
                    {"id": str(item.id), "field_type": item.field_type, "status": item.status}
                    for item in conflicts
                ],
                "questions": [
                    {
                        "id": str(item.id),
                        "requirement_key": item.requirement_key,
                        "text": item.question_text,
                        "status": item.status,
                    }
                    for item in questions
                ],
            },
            "retrieval": retrieval,
            "ai_content": {
                "drafts": [
                    {
                        "origin": "AI_GENERATED",
                        "id": str(draft.id),
                        "version": draft.version,
                        "content": draft.content_json,
                        "reviewer_status": draft.reviewer_status,
                        "provenance": draft.provenance_json,
                    }
                    for draft in drafts
                ],
                "policy_decisions": [
                    {
                        "ai_run_id": str(item.ai_run_id),
                        "check_type": item.check_type,
                        "outcome": item.outcome,
                    }
                    for item in policy_decisions
                ],
            },
            "human_content": {
                "active_note": (
                    {"id": str(note.id), "version": note.version, "content": note.content}
                    if note
                    else None
                ),
                "review_decisions": [
                    {
                        "id": str(item.id),
                        "decision_type": item.decision_type,
                        "draft_id": str(item.draft_id) if item.draft_id else None,
                        "case_version": item.case_version,
                    }
                    for item in decisions
                ],
            },
            "escalations": [
                {"id": str(item.id), "status": item.status, "reason": item.reason}
                for item in escalations
            ],
            "referrals": {
                "packages": [
                    {"id": str(item.id), "version": item.version, "status": item.status}
                    for item in packages
                ],
                "handoffs": [
                    {
                        "id": str(item.id),
                        "status": item.status,
                        "recipient_id": str(item.recipient_id),
                        "channel": item.channel,
                    }
                    for item in handoffs
                ],
            },
        }
