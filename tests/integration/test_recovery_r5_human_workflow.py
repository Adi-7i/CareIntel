"""Synthetic persisted human-review, referral, and acknowledgement workflow."""

from __future__ import annotations

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from careintel.application.auth.consent_service import ConsentService
from careintel.application.escalation.escalation_service import EscalationService
from careintel.application.handoff.handoff_service import HandoffService
from careintel.application.handoff.referral_service import ReferralPackageService
from careintel.application.review.decision_service import ReviewDecisionService
from careintel.application.review.draft_service import DraftReviewService
from careintel.application.review.review_service import ReviewService
from careintel.application.review.workspace_service import WorkspaceService
from careintel.application.workflow.outbox_dispatcher import UnifiedOutboxDispatcher
from careintel.core.config import Settings
from careintel.core.database import build_engine
from careintel.core.errors import AuthorizationError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.case.states import CaseState
from careintel.domain.handoff.states import HandoffStatus
from careintel.domain.review.states import ReviewDecisionType, ReviewQueueStatus
from careintel.persistence.models.ai import AIDraftORM, AIRunORM
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM, CaseOutboxORM, EncounterORM
from careintel.persistence.models.consent import ConsentORM
from careintel.persistence.models.evidence import EvidenceORM, TextContentORM
from careintel.persistence.models.handoff import HandoffORM, RecipientORM
from careintel.persistence.models.review import DraftEditVersionORM, ReviewDecisionORM
from careintel.persistence.models.user import UserORM
from careintel.persistence.repositories.ai_repo import AIRepository
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_history_repo import CaseHistoryRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.consent_repo import ConsentRepository
from careintel.persistence.repositories.encounter_repo import EncounterRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.handoff_repo import HandoffRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository
from careintel.persistence.repositories.retrieval_repo import RetrievalRepository
from careintel.persistence.repositories.review_repo import ReviewRepository
from careintel.persistence.repositories.structuring_repo import StructuringRepository
from careintel.persistence.repositories.text_content_repo import TextContentRepository
from careintel.workers.executor import execute_durable_task
from careintel.workers.handoff_tasks import _handle_handoff

pytestmark = pytest.mark.integration


async def test_human_review_escalation_referral_acknowledgement_and_isolation(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    if "test:test@" in settings.database_url.get_secret_value():
        pytest.skip("R5 integration test requires configured PostgreSQL.")

    engine = build_engine(settings)
    connection = await engine.connect()
    outer = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = session_factory()
    try:
        now = datetime.datetime.now(datetime.UTC)
        encounter_time = now.replace(tzinfo=None)
        reviewer_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        facility_id = uuid.uuid4()
        case_id = uuid.uuid4()
        encounter_id = uuid.uuid4()
        evidence_id = uuid.uuid4()
        run_id = uuid.uuid4()
        draft_id = uuid.uuid4()
        recipient_id = uuid.uuid4()
        correlation_id = f"r5-{uuid.uuid4()}"

        session.add_all(
            [
                UserORM(
                    id=reviewer_id,
                    email=f"r5-reviewer-{reviewer_id}@example.invalid",
                    display_name="Synthetic R5 Reviewer",
                    password_hash="synthetic-not-a-credential",
                    is_active=True,
                ),
                UserORM(
                    id=subject_id,
                    email=f"r5-subject-{subject_id}@example.invalid",
                    display_name="Synthetic R5 Subject",
                    password_hash="synthetic-not-a-credential",
                    is_active=True,
                ),
            ]
        )
        await session.flush()
        session.add(
            CaseORM(
                id=case_id,
                synthetic_subject_id=subject_id,
                facility_id=facility_id,
                state=CaseState.REVIEW_PENDING.value,
                version=1,
                opened_by=reviewer_id,
            )
        )
        await session.flush()
        session.add_all(
            [
                EncounterORM(
                    id=encounter_id,
                    case_id=case_id,
                    encounter_type="synthetic_review",
                    occurred_at=encounter_time,
                    created_by=reviewer_id,
                ),
                ConsentORM(
                    id=uuid.uuid4(),
                    subject_id=subject_id,
                    purpose="ai_analysis",
                    notice_version="1.0",
                    state="ACTIVE",
                    captured_by=reviewer_id,
                    captured_at=now,
                ),
                ConsentORM(
                    id=uuid.uuid4(),
                    subject_id=subject_id,
                    purpose="referral",
                    notice_version="1.0",
                    state="ACTIVE",
                    captured_by=reviewer_id,
                    captured_at=now,
                ),
                EvidenceORM(
                    id=evidence_id,
                    case_id=case_id,
                    encounter_id=encounter_id,
                    modality="TEXT",
                    state="READY",
                    content_type="text/plain",
                    size_bytes=31,
                    sha256_checksum=uuid.uuid4().hex,
                    created_by=reviewer_id,
                    provenance={"fixture_id": "synthetic-r5"},
                ),
                RecipientORM(
                    id=recipient_id,
                    name="Synthetic Referral Recipient",
                    recipient_type="synthetic-channel",
                    config_json={"provider": "demo"},
                    is_active=True,
                ),
            ]
        )
        await session.flush()
        session.add(
            TextContentORM(
                id=uuid.uuid4(),
                evidence_id=evidence_id,
                content="Synthetic review-only evidence.",
                word_count=4,
                char_count=31,
            )
        )
        session.add(
            AIRunORM(
                id=run_id,
                case_id=case_id,
                actor_id=reviewer_id,
                task_type="CASE_SUMMARY",
                provider="synthetic-provider",
                model="synthetic-model",
                prompt_version="test-v1",
                schema_version="test-v1",
                status="COMPLETED",
                input_hash=uuid.uuid4().hex,
                usage_json={},
            )
        )
        await session.flush()
        session.add(
            AIDraftORM(
                id=draft_id,
                ai_run_id=run_id,
                content_json={"summary": "AI-generated advisory draft."},
                validation_status="ACCEPTED",
                validation_errors=[],
                provenance_json=[
                    {
                        "claim_text": "Synthetic advisory claim",
                        "status": "SUPPORTED",
                        "supporting_source_ids": [str(evidence_id)],
                    }
                ],
                reviewer_status="DRAFT",
                version=1,
            )
        )
        await session.flush()

        permissions = {permission.value for permission in Permission}
        reviewer = UserContext(
            id=reviewer_id,
            is_active=True,
            roles={"synthetic-reviewer"},
            permissions=permissions,
            role_facilities={"synthetic-reviewer": facility_id},
        )
        other_facility_actor = UserContext(
            id=uuid.uuid4(),
            is_active=True,
            roles={"synthetic-reviewer"},
            permissions=permissions,
            role_facilities={"synthetic-reviewer": uuid.uuid4()},
        )
        audit_repo = AuditRepository(session)
        consent_service = ConsentService(ConsentRepository(session), audit_repo)
        case_repo = CaseRepository(session)
        review_repo = ReviewRepository(session)
        ai_repo = AIRepository(session)
        history_repo = CaseHistoryRepository(session)
        outbox_repo = CaseOutboxRepository(session)
        handoff_repo = HandoffRepository(session)

        user_repo = AsyncMock()
        user_repo.get_user_context.return_value = reviewer
        review_service = ReviewService(
            review_repo,
            case_repo,
            EncounterRepository(session),
            user_repo,
            consent_service,
            audit_repo,
        )
        queue = await review_service.enter_review_queue(
            case_id, reviewer, correlation_id, encounter_id
        )
        assert queue.encounter_id == encounter_id
        queue = await review_service.assign_reviewer(
            case_id, reviewer_id, queue.version, reviewer, correlation_id
        )
        queue = await review_service.start_review(case_id, queue.version, reviewer, correlation_id)
        assert queue.status == ReviewQueueStatus.IN_REVIEW.value

        workspace_service = WorkspaceService(
            case_repo,
            review_repo,
            EncounterRepository(session),
            EvidenceRepository(session),
            TextContentRepository(session),
            ProcessingRepository(session),
            StructuringRepository(session),
            RetrievalRepository(session),
            ai_repo,
            handoff_repo,
            consent_service,
            audit_repo,
        )
        workspace = await workspace_service.get_reviewer_workspace(
            case_id, reviewer, correlation_id
        )
        assert workspace["original_evidence"][0]["origin"] == "ORIGINAL_EVIDENCE"
        assert workspace["ai_content"]["drafts"][0]["origin"] == "AI_GENERATED"
        with pytest.raises(AuthorizationError):
            await workspace_service.get_reviewer_workspace(
                case_id, other_facility_actor, correlation_id
            )

        escalation_service = EscalationService(
            review_repo,
            case_repo,
            history_repo,
            outbox_repo,
            consent_service,
            audit_repo,
        )
        escalation = await escalation_service.create_escalation(
            case_id,
            "Synthetic manual escalation",
            expected_case_version=1,
            expected_queue_version=queue.version,
            actor=reviewer,
            correlation_id=correlation_id,
        )
        case = await case_repo.get_by_id(case_id)
        assert case is not None and case.state == CaseState.ESCALATED.value
        escalation = await escalation_service.resolve_escalation(
            escalation.id,
            "Synthetic resolution",
            expected_case_version=case.version,
            expected_queue_version=queue.version,
            actor=reviewer,
            correlation_id=correlation_id,
        )
        assert escalation.status == "RESOLVED"

        draft_service = DraftReviewService(
            ai_repo, review_repo, case_repo, consent_service, audit_repo
        )
        draft = await draft_service.edit_draft(
            draft_id,
            {"summary": "Human-edited advisory content."},
            "Synthetic reviewer edit",
            expected_draft_version=1,
            expected_queue_version=queue.version,
            actor=reviewer,
            correlation_id=correlation_id,
        )
        assert draft.reviewer_status == "APPROVED"
        edit = await review_repo.get_latest_edit_for_draft(draft_id)
        assert edit is not None and edit.content_origin == "HUMAN_EDITED"

        case = await case_repo.get_by_id(case_id)
        decision_service = ReviewDecisionService(
            review_repo,
            case_repo,
            ai_repo,
            history_repo,
            outbox_repo,
            consent_service,
            audit_repo,
        )
        assert case is not None
        decision = await decision_service.submit_decision(
            case_id,
            draft_id,
            ReviewDecisionType.REFER,
            "Synthetic human referral approval",
            expected_case_version=case.version,
            expected_queue_version=queue.version,
            expected_draft_version=draft.version,
            actor=reviewer,
            correlation_id=correlation_id,
        )
        assert decision.reviewer_id == reviewer_id
        assert decision.draft_version == draft.version

        referral_service = ReferralPackageService(
            handoff_repo,
            case_repo,
            EvidenceRepository(session),
            review_repo,
            ai_repo,
            consent_service,
            audit_repo,
        )
        package = await referral_service.prepare_referral_package(
            case_id, [evidence_id], reviewer, correlation_id
        )
        assert package.content_json["approved_reviewer_content"] == {
            "summary": "Human-edited advisory content."
        }
        package = await referral_service.finalize_package(package.id, reviewer, correlation_id)
        assert package.status == "FINALIZED"

        handoff_service = HandoffService(
            handoff_repo,
            case_repo,
            history_repo,
            outbox_repo,
            consent_service,
            audit_repo,
        )
        handoff = await handoff_service.initiate_handoff(
            package.id, recipient_id, reviewer, correlation_id
        )
        handoff = await handoff_service.send_handoff(
            handoff.id, handoff.version, reviewer, correlation_id
        )
        send_event = (
            await session.execute(
                select(CaseOutboxORM).where(
                    CaseOutboxORM.case_id == case_id,
                    CaseOutboxORM.event_type == "HANDOFF_SEND_REQUESTED",
                )
            )
        ).scalar_one()
        send_event.occurred_at = datetime.datetime(1800, 1, 1)
        await session.commit()

        broker_send = MagicMock()
        monkeypatch.setattr(
            "careintel.application.workflow.outbox_dispatcher.celery_app.send_task",
            broker_send,
        )
        dispatcher = UnifiedOutboxDispatcher(session_factory, dispatcher_id="synthetic-r5")
        dispatcher._MODELS = {"case": CaseOutboxORM}
        assert await dispatcher.dispatch_once(batch_size=1) == 1
        send_event = await session.get(CaseOutboxORM, send_event.id, populate_existing=True)
        assert send_event is not None and send_event.celery_task_id is not None
        broker_send.assert_called_once()

        monkeypatch.setattr(
            "careintel.workers.executor.get_session_factory", lambda: session_factory
        )
        monkeypatch.setattr(
            "careintel.workers.executor.load_worker_actor",
            AsyncMock(return_value=reviewer),
        )
        task_result = await execute_durable_task(
            send_event.celery_task_id,
            _handle_handoff,
            celery_task_id=send_event.celery_task_id,
        )
        assert task_result is not None and task_result["status"] == HandoffStatus.SENT.value
        handoff = await session.get(HandoffORM, handoff.id, populate_existing=True)
        assert handoff is not None
        assert handoff.status == HandoffStatus.SENT.value
        case = await session.get(CaseORM, case_id, populate_existing=True)
        assert case is not None and case.state == CaseState.REFERRED.value

        handoff = await handoff_service.record_acknowledgement(
            handoff.id,
            "synthetic-acknowledgement",
            handoff.version,
            reviewer,
            correlation_id,
        )
        assert handoff.status == HandoffStatus.ACKNOWLEDGED.value
        assert case.state != CaseState.COMPLETED.value
        handoff = await handoff_service.complete_handoff(
            handoff.id,
            handoff.version,
            case.version,
            reviewer,
            correlation_id,
        )
        assert handoff.status == HandoffStatus.COMPLETED.value
        assert case.state == CaseState.COMPLETED.value

        assert (
            await session.scalar(
                select(func.count())
                .select_from(ReviewDecisionORM)
                .where(ReviewDecisionORM.case_id == case_id)
            )
            == 1
        )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(DraftEditVersionORM)
                .where(DraftEditVersionORM.draft_id == draft_id)
            )
            == 1
        )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(AuditLogORM)
                .where(AuditLogORM.correlation_id == correlation_id)
            )
            >= 12
        )
    finally:
        await session.close()
        await outer.rollback()
        await connection.close()
        await engine.dispose()
