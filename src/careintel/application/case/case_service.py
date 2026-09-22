"""
Case Management application service.
"""

from __future__ import annotations

import datetime
import uuid

from ulid import ULID

from careintel.core.errors import (
    AuthorizationError,
    ConcurrencyError,
    InvalidTransitionError,
    NotFoundError,
)
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.domain.case.commands import CreateCaseCommand, TransitionCaseCommand
from careintel.domain.case.models import CaseAggregate
from careintel.domain.case.state_machine import CaseStateMachine
from careintel.domain.case.states import CaseState
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import CaseORM, CaseOutboxORM, CaseStateHistoryORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_history_repo import CaseHistoryRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository


class CaseService:
    """Orchestrates Case Management use cases."""

    def __init__(
        self,
        case_repo: CaseRepository,
        history_repo: CaseHistoryRepository,
        outbox_repo: CaseOutboxRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self.case_repo = case_repo
        self.history_repo = history_repo
        self.outbox_repo = outbox_repo
        self.audit_repo = audit_repo

    def _to_domain(self, orm: CaseORM) -> CaseAggregate:
        """Map ORM to domain aggregate."""
        return CaseAggregate(
            case_id=orm.id,
            synthetic_subject_id=orm.synthetic_subject_id,
            facility_id=orm.facility_id,
            state=CaseState(orm.state),
            version=orm.version,
            opened_by=orm.opened_by,
            assigned_to=orm.assigned_to,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def create_case(
        self,
        cmd: CreateCaseCommand,
        actor: UserContext,
    ) -> CaseAggregate:
        """
        Create a new Case.

        Consent is verified at the API boundary before passing here.
        This simply sets up the initial case state.
        """
        if not AuthorizationPolicy.evaluate(
            actor,
            Permission.CASE_WRITE,
            facility_scope=cmd.facility_id,
        ):
            raise AuthorizationError("Actor is not authorized for the requested facility.")

        case_id = uuid.uuid4()
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

        # 1. Create ORM
        case_orm = CaseORM(
            id=case_id,
            synthetic_subject_id=cmd.synthetic_subject_id,
            facility_id=cmd.facility_id,
            state=CaseState.CREATED.value,
            version=1,
            opened_by=cmd.opened_by,
            created_at=now,
            updated_at=now,
        )

        # 2. Initial history
        history_orm = CaseStateHistoryORM(
            id=uuid.uuid4(),
            case_id=case_id,
            from_state="NONE",
            to_state=CaseState.CREATED.value,
            actor_id=cmd.opened_by,
            aggregate_version=1,
            transitioned_at=now,
            command_type="CreateCaseCommand",
        )

        # 3. Outbox event
        outbox_orm = CaseOutboxORM(
            id=str(ULID()),
            event_type="CASE_CREATED",
            event_version=1,
            occurred_at=now,
            producer="careintel.case_service",
            correlation_id=cmd.correlation_id,
            case_id=case_id,
            actor_id=cmd.opened_by,
            aggregate_version=1,
            payload={
                "synthetic_subject_id": str(cmd.synthetic_subject_id),
                "facility_id": str(cmd.facility_id) if cmd.facility_id else None,
                "state": CaseState.CREATED.value,
            },
        )

        # Execute
        await self.case_repo.create(case_orm)
        await self.history_repo.append(history_orm)
        await self.outbox_repo.append(outbox_orm)

        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.CASE_CREATED.value,
                actor_id=actor.id,
                target_id=case_id,
                target_type="case",
                correlation_id=cmd.correlation_id,
                outcome="SUCCESS",
            )
        )

        return self._to_domain(case_orm)

    async def get_case(self, case_id: uuid.UUID, actor: UserContext) -> CaseAggregate:
        """Get a case and enforce object-level authorization."""
        case_orm = await self.case_repo.get_by_id(case_id)
        if not case_orm:
            raise NotFoundError("Case not found.")

        # Check facility scope
        granted = AuthorizationPolicy.evaluate(
            actor, Permission.CASE_READ, facility_scope=case_orm.facility_id
        )
        if not granted:
            raise NotFoundError("Case not found.")  # Mask 403 as 404 for object discovery

        return self._to_domain(case_orm)

    async def transition_state(
        self,
        cmd: TransitionCaseCommand,
        actor: UserContext,
    ) -> CaseAggregate:
        """
        Transition a case state.
        Uses optimistic concurrency to ensure we don't overwrite a concurrent update.
        """
        case_orm = await self.case_repo.get_for_update(cmd.case_id, cmd.expected_version)
        if not case_orm:
            # Did it exist at all?
            exists = await self.case_repo.get_by_id(cmd.case_id)
            if not exists:
                raise NotFoundError("Case not found.")

            # It exists, but version mismatched
            await self.audit_repo.append(
                AuditLogORM(
                    event_type=AuditEventType.CASE_CONCURRENCY_CONFLICT.value,
                    actor_id=actor.id,
                    target_id=cmd.case_id,
                    target_type="case",
                    correlation_id=cmd.correlation_id,
                    outcome="FAILURE",
                    detail={"expected": cmd.expected_version, "actual": exists.version},
                )
            )
            raise ConcurrencyError()

        # Object-level authorization
        granted = AuthorizationPolicy.evaluate(
            actor, Permission.CASE_WRITE, facility_scope=case_orm.facility_id
        )
        if not granted:
            await self.audit_repo.append(
                AuditLogORM(
                    event_type=AuditEventType.CASE_AUTH_DENIED.value,
                    actor_id=actor.id,
                    target_id=cmd.case_id,
                    target_type="case",
                    correlation_id=cmd.correlation_id,
                    outcome="DENIED",
                )
            )
            raise NotFoundError("Case not found.")

        # State Machine Validation
        try:
            CaseStateMachine.validate_transition(case_orm.state, cmd.to_state)
        except InvalidTransitionError as e:
            await self.audit_repo.append(
                AuditLogORM(
                    event_type=AuditEventType.CASE_INVALID_TRANSITION.value,
                    actor_id=actor.id,
                    target_id=cmd.case_id,
                    target_type="case",
                    correlation_id=cmd.correlation_id,
                    outcome="DENIED",
                    detail={"from_state": case_orm.state, "to_state": cmd.to_state},
                )
            )
            raise e

        # Transition
        new_version = cmd.expected_version + 1
        to_state_str = str(cmd.to_state)
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

        updated = await self.case_repo.update_state(cmd.case_id, to_state_str, new_version)
        if not updated:
            raise ConcurrencyError()

        # History
        history_orm = CaseStateHistoryORM(
            id=uuid.uuid4(),
            case_id=cmd.case_id,
            from_state=case_orm.state,
            to_state=to_state_str,
            actor_id=actor.id,
            aggregate_version=new_version,
            transitioned_at=now,
            reason=cmd.reason,
            command_type="TransitionCaseCommand",
        )
        await self.history_repo.append(history_orm)

        # Outbox
        outbox_orm = CaseOutboxORM(
            id=str(ULID()),
            event_type="CASE_STATE_TRANSITION",
            event_version=1,
            occurred_at=now,
            producer="careintel.case_service",
            correlation_id=cmd.correlation_id,
            case_id=cmd.case_id,
            actor_id=actor.id,
            aggregate_version=new_version,
            payload={
                "from_state": case_orm.state,
                "to_state": to_state_str,
                "reason": cmd.reason,
            },
        )
        await self.outbox_repo.append(outbox_orm)

        # Audit
        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.CASE_STATE_TRANSITION.value,
                actor_id=actor.id,
                target_id=cmd.case_id,
                target_type="case",
                correlation_id=cmd.correlation_id,
                outcome="SUCCESS",
                detail={"from_state": case_orm.state, "to_state": to_state_str},
            )
        )

        # Return updated domain object
        case_orm.state = to_state_str
        case_orm.version = new_version
        case_orm.updated_at = now
        return self._to_domain(case_orm)

    async def get_state_history(
        self, case_id: uuid.UUID, actor: UserContext
    ) -> list[CaseStateHistoryORM]:
        """Get history and enforce object-level authorization."""
        case_orm = await self.case_repo.get_by_id(case_id)
        if not case_orm:
            raise NotFoundError("Case not found.")

        granted = AuthorizationPolicy.evaluate(
            actor, Permission.CASE_READ, facility_scope=case_orm.facility_id
        )
        if not granted:
            raise NotFoundError("Case not found.")

        return await self.history_repo.list_for_case(case_id)
