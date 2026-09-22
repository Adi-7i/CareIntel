"""
Evidence Management application service.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import IO

from ulid import ULID

from careintel.application.case.case_service import CaseService
from careintel.application.evidence.file_validator import FileValidator
from careintel.core.errors import (
    DuplicateEvidenceError,
    NotFoundError,
    StorageError,
    UnsupportedFileTypeError,
)
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.case.commands import TransitionCaseCommand
from careintel.domain.case.states import CaseState
from careintel.domain.consent.models import ConsentContext
from careintel.domain.consent.policy import ConsentPolicy
from careintel.domain.consent.purpose import ConsentPurpose
from careintel.domain.evidence.commands import (
    RegisterTextEvidenceCommand,
    UploadFileEvidenceCommand,
)
from careintel.domain.evidence.models import EvidenceAggregate
from careintel.domain.evidence.state_machine import EvidenceStateMachine
from careintel.domain.evidence.states import EvidenceState
from careintel.infrastructure.scanner.port import ContentScannerPort, ScanResult
from careintel.infrastructure.storage.port import BlobStoragePort
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM
from careintel.persistence.models.evidence import (
    EvidenceORM,
    EvidenceOutboxORM,
    EvidenceStateHistoryORM,
    TextContentORM,
)
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.consent_repo import ConsentRepository
from careintel.persistence.repositories.evidence_history_repo import EvidenceHistoryRepository
from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.text_content_repo import TextContentRepository


class EvidenceService:
    """Orchestrates Evidence intake use cases."""

    def __init__(
        self,
        case_repo: CaseRepository,
        consent_repo: ConsentRepository,
        evidence_repo: EvidenceRepository,
        text_repo: TextContentRepository,
        history_repo: EvidenceHistoryRepository,
        outbox_repo: EvidenceOutboxRepository,
        audit_repo: AuditRepository,
        case_service: CaseService,
        blob_provider: BlobStoragePort,
        scanner: ContentScannerPort,
        file_validator: FileValidator,
        sas_ttl_minutes: int = 15,
    ) -> None:
        self.case_repo = case_repo
        self.consent_repo = consent_repo
        self.evidence_repo = evidence_repo
        self.text_repo = text_repo
        self.history_repo = history_repo
        self.outbox_repo = outbox_repo
        self.audit_repo = audit_repo
        self.case_service = case_service
        self.blob_provider = blob_provider
        self.scanner = scanner
        self.file_validator = file_validator
        self.sas_ttl_minutes = sas_ttl_minutes

    def _to_domain(self, orm: EvidenceORM) -> EvidenceAggregate:
        """Map ORM to domain aggregate."""
        return EvidenceAggregate(
            evidence_id=orm.id,
            case_id=orm.case_id,
            encounter_id=orm.encounter_id,
            modality=orm.modality,  # type: ignore
            state=EvidenceState(orm.state),
            original_filename=orm.original_filename,
            content_type=orm.content_type,
            size_bytes=orm.size_bytes,
            sha256_checksum=orm.sha256_checksum,
            source_language=orm.source_language,
            storage_key=orm.storage_key,
            created_by=orm.created_by,
            created_at=orm.created_at,
            provenance=orm.provenance,
        )

    async def _get_authorized_case(
        self, case_id: uuid.UUID, user: UserContext, required_permission: str
    ) -> CaseORM:
        """Fetch the case and assert permissions."""
        case_orm = await self.case_repo.get_by_id(case_id)
        if not case_orm:
            raise NotFoundError(f"Case {case_id} not found.")

        granted = AuthorizationPolicy.evaluate(
            actor=user,
            action=required_permission,
            facility_scope=case_orm.facility_id,
        )
        if not granted:
            # Mask 403 as 404 for object discovery
            raise NotFoundError(f"Case {case_id} not found.")
        return case_orm

    async def _require_data_processing_consent(
        self,
        consent_id: uuid.UUID,
        case_orm: CaseORM,
    ) -> None:
        """Validate that the supplied consent authorizes this case subject."""
        consent_orm = await self.consent_repo.get_by_id(consent_id)
        consent = None
        if consent_orm is not None:
            consent = ConsentContext(
                id=consent_orm.id,
                subject_id=consent_orm.subject_id,
                purpose=consent_orm.purpose,
                notice_version=consent_orm.notice_version,
                state=consent_orm.state,
            )
        ConsentPolicy.require_active(
            consent=consent,
            subject_id=case_orm.synthetic_subject_id,
            purpose=ConsentPurpose.DATA_PROCESSING,
            required_notice_version="1.0",
        )

    async def _append_audit(
        self,
        event_type: str,
        actor_id: uuid.UUID,
        correlation_id: str,
        target_id: uuid.UUID,
        outcome: str = "SUCCESS",
        detail: dict[str, str | int] | None = None,
    ) -> None:
        """Helper to append an audit log entry."""
        audit = AuditLogORM(
            event_type=event_type,
            actor_id=actor_id,
            correlation_id=correlation_id,
            target_id=target_id,
            target_type="evidence",
            outcome=outcome,
            detail=detail,
        )
        await self.audit_repo.append(audit)

    async def register_text_evidence(
        self, cmd: RegisterTextEvidenceCommand, user: UserContext
    ) -> EvidenceAggregate:
        """Register text-based evidence and transition case state if needed."""
        case_orm = await self._get_authorized_case(cmd.case_id, user, Permission.EVIDENCE_WRITE)
        await self._require_data_processing_consent(cmd.consent_id, case_orm)

        # Create Evidence ORM
        evidence_orm = EvidenceORM(
            case_id=cmd.case_id,
            encounter_id=cmd.encounter_id,
            modality="TEXT",
            state=EvidenceState.READY,
            content_type="text/plain",
            size_bytes=len(cmd.text_content.encode("utf-8")),
            source_language=cmd.source_language,
            created_by=cmd.actor_id,
            provenance={"source": "direct_input"},
        )
        await self.evidence_repo.create(evidence_orm)

        # Create immutable Text Content
        text_orm = TextContentORM(
            evidence_id=evidence_orm.id,
            content=cmd.text_content,
            char_count=len(cmd.text_content),
            word_count=len(cmd.text_content.split()),
        )
        await self.text_repo.create(text_orm)

        # Dispatch case state transition if needed
        if case_orm.state == CaseState.CONSENTED:
            # Note: In a real distributed system this might be eventually consistent,
            # but we use CaseService to do it safely here.
            transition_cmd = TransitionCaseCommand(
                case_id=cmd.case_id,
                actor_id=cmd.actor_id,
                from_state=CaseState.CONSENTED,
                to_state=CaseState.INPUT_RECEIVED,
                expected_version=case_orm.version,
                reason="Initial text evidence received",
                correlation_id=cmd.correlation_id,
            )
            # This commits its own state!
            await self.case_service.transition_state(transition_cmd, user)

        # Outbox event
        outbox = EvidenceOutboxORM(
            id=str(ULID()),
            event_type="evidence.text.registered",
            producer="careintel.evidence",
            correlation_id=cmd.correlation_id,
            evidence_id=evidence_orm.id,
            case_id=cmd.case_id,
            actor_id=cmd.actor_id,
            payload={"modality": "TEXT"},
        )
        await self.outbox_repo.append(outbox)

        # Audit
        await self._append_audit(
            AuditEventType.EVIDENCE_TEXT_CREATED,
            cmd.actor_id,
            cmd.correlation_id,
            evidence_orm.id,
        )

        return self._to_domain(evidence_orm)

    async def start_file_upload(
        self, cmd: UploadFileEvidenceCommand, user: UserContext
    ) -> EvidenceAggregate:
        """Start a multipart file upload."""
        case_orm = await self._get_authorized_case(cmd.case_id, user, Permission.EVIDENCE_WRITE)
        await self._require_data_processing_consent(cmd.consent_id, case_orm)

        # Validate extension first before doing anything
        sanitized_filename = self.file_validator.validate_extension(cmd.declared_filename)

        evidence_orm = EvidenceORM(
            case_id=cmd.case_id,
            encounter_id=cmd.encounter_id,
            modality=cmd.modality,
            state=EvidenceState.PENDING_UPLOAD,
            original_filename=sanitized_filename,
            content_type=cmd.declared_content_type,
            size_bytes=0,  # To be filled during stream
            created_by=cmd.actor_id,
            provenance={"declared_type": cmd.declared_content_type},
        )
        await self.evidence_repo.create(evidence_orm)

        await self._append_audit(
            AuditEventType.EVIDENCE_UPLOAD_STARTED,
            cmd.actor_id,
            cmd.correlation_id,
            evidence_orm.id,
        )
        return self._to_domain(evidence_orm)

    async def complete_file_upload(
        self,
        evidence_id: uuid.UUID,
        file_stream: IO[bytes],
        user: UserContext,
        correlation_id: str,
    ) -> EvidenceAggregate:
        """Stream file, validate magic bytes, compute SHA256, and upload to Azure."""
        evidence_orm = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence_orm:
            raise NotFoundError(f"Evidence {evidence_id} not found.")

        await self._get_authorized_case(evidence_orm.case_id, user, Permission.EVIDENCE_WRITE)

        if evidence_orm.state != EvidenceState.PENDING_UPLOAD:
            raise UnsupportedFileTypeError("Evidence is not in PENDING_UPLOAD state.")

        # 1. Stream and Validate
        sha256, magic_mime, total_size = await self.file_validator.stream_and_validate(file_stream)
        self.file_validator.validate_mime_consistency(
            filename=evidence_orm.original_filename or "",
            declared_mime=evidence_orm.content_type,
            detected_mime=magic_mime,
        )

        # 2. Check Duplicates
        existing = await self.evidence_repo.get_by_checksum(evidence_orm.case_id, str(sha256))
        if existing and existing.id != evidence_id:
            await self._append_audit(
                AuditEventType.EVIDENCE_DUPLICATE_DETECTED,
                user.id,
                correlation_id,
                evidence_id,
            )
            # Delete the pending record
            await self.evidence_repo.update_state(evidence_id, EvidenceState.FAILED)
            raise DuplicateEvidenceError("Exact file has already been uploaded to this case.")

        # 3. DRES Key structure
        key = (
            f"cases/{evidence_orm.case_id}/{evidence_orm.modality.lower()}s/{evidence_id}/original"
        )

        # 4. Azure Blob Upload (stream to Storage)
        await self.blob_provider.upload(
            key=key,
            data=self._async_file_reader(file_stream),
            content_type=magic_mime,
            size=total_size,
        )

        # 5. Update Evidence ORM
        evidence_orm.sha256_checksum = str(sha256)
        evidence_orm.size_bytes = total_size
        evidence_orm.content_type = str(magic_mime)
        evidence_orm.storage_key = key
        await self.evidence_repo.update_storage_key(evidence_id, key)

        # Advance State
        await self._transition_evidence_state(
            evidence_orm,
            EvidenceState.STORED,
            user.id,
            correlation_id,
            "File uploaded successfully",
        )

        # 6. Outbox Event
        outbox = EvidenceOutboxORM(
            id=str(ULID()),
            event_type="evidence.file.uploaded",
            producer="careintel.evidence",
            correlation_id=correlation_id,
            evidence_id=evidence_id,
            case_id=evidence_orm.case_id,
            actor_id=user.id,
            payload={"modality": evidence_orm.modality, "storage_key": key},
        )
        await self.outbox_repo.append(outbox)

        await self._append_audit(
            AuditEventType.EVIDENCE_UPLOAD_ACCEPTED,
            user.id,
            correlation_id,
            evidence_id,
        )

        # 7. Scan content (if real scanner is used, otherwise stays STORED)
        scan_result = await self.scanner.scan(evidence_id, key)
        if scan_result == ScanResult.CLEAN:
            await self._transition_evidence_state(
                evidence_orm, EvidenceState.READY, user.id, correlation_id, "Scan CLEAN"
            )
        elif scan_result == ScanResult.REJECTED:
            await self._transition_evidence_state(
                evidence_orm, EvidenceState.QUARANTINED, user.id, correlation_id, "Scan REJECTED"
            )

        return self._to_domain(evidence_orm)

    async def _async_file_reader(self, file_stream: IO[bytes]) -> AsyncIterator[bytes]:
        """Convert a synchronous file stream to an AsyncIterator for Azure."""
        chunk_size = 65536
        while True:
            chunk = file_stream.read(chunk_size)
            if not chunk:
                break
            yield chunk

    async def _transition_evidence_state(
        self,
        evidence_orm: EvidenceORM,
        to_state: EvidenceState,
        actor_id: uuid.UUID,
        correlation_id: str,
        reason: str,
    ) -> None:
        """Internal helper to safely transition state."""
        EvidenceStateMachine.validate_transition(evidence_orm.state, to_state)

        history = EvidenceStateHistoryORM(
            evidence_id=evidence_orm.id,
            from_state=evidence_orm.state,
            to_state=to_state,
            actor_id=actor_id,
            reason=reason,
        )
        await self.history_repo.append(history)
        await self.evidence_repo.update_state(evidence_orm.id, to_state.value)
        evidence_orm.state = to_state.value

        await self._append_audit(
            AuditEventType.EVIDENCE_STATE_TRANSITION,
            actor_id,
            correlation_id,
            evidence_orm.id,
            detail={"from": history.from_state, "to": to_state},
        )

    async def get_evidence(self, evidence_id: uuid.UUID, user: UserContext) -> EvidenceAggregate:
        """Get an evidence aggregate by ID."""
        evidence_orm = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence_orm:
            raise NotFoundError(f"Evidence {evidence_id} not found.")

        # Object-level authorization
        await self._get_authorized_case(evidence_orm.case_id, user, Permission.EVIDENCE_READ)
        return self._to_domain(evidence_orm)

    async def list_for_case(self, case_id: uuid.UUID, user: UserContext) -> list[EvidenceAggregate]:
        """List all evidence for a specific case."""
        await self._get_authorized_case(case_id, user, Permission.EVIDENCE_READ)
        orms = await self.evidence_repo.get_by_case_id(case_id)
        return [self._to_domain(o) for o in orms]

    async def generate_secure_download_url(
        self, evidence_id: uuid.UUID, user: UserContext, correlation_id: str
    ) -> str:
        """Generate a short-lived SAS URL for downloading original evidence."""
        evidence_orm = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence_orm:
            raise NotFoundError(f"Evidence {evidence_id} not found.")

        await self._get_authorized_case(evidence_orm.case_id, user, Permission.EVIDENCE_READ)

        if evidence_orm.state != EvidenceState.READY:
            raise StorageError("Evidence is not READY for download.")

        if not evidence_orm.storage_key:
            raise StorageError("Storage key missing for evidence.")

        sas_url = await self.blob_provider.generate_sas_url(
            evidence_orm.storage_key, ttl_seconds=self.sas_ttl_minutes * 60
        )

        await self._append_audit(
            AuditEventType.EVIDENCE_DOWNLOAD_AUTHORIZED,
            user.id,
            correlation_id,
            evidence_id,
        )
        return sas_url
