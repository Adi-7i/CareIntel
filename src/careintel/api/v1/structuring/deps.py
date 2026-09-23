"""
Dependencies for the Structuring API.
"""

from typing import Annotated

from fastapi import Depends

from careintel.api.deps import DbSessionDep, SettingsDep, get_consent_service
from careintel.application.auth.consent_service import ConsentService
from careintel.application.structuring.structuring_service import StructuringService
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository
from careintel.persistence.repositories.structuring_repo import StructuringRepository


def get_structuring_repo(session: DbSessionDep) -> StructuringRepository:
    return StructuringRepository(session)


StructuringRepoDep = Annotated[StructuringRepository, Depends(get_structuring_repo)]


def get_structuring_service(
    session: DbSessionDep,
    repo: StructuringRepoDep,
    consent_service: Annotated[ConsentService, Depends(get_consent_service)],
    settings: SettingsDep,
) -> StructuringService:
    return StructuringService(
        structuring_repo=repo,
        processing_repo=ProcessingRepository(session),
        case_repo=CaseRepository(session),
        case_outbox_repo=CaseOutboxRepository(session),
        audit_repo=AuditRepository(session),
        consent_service=consent_service,
        settings=settings,
    )


StructuringServiceDep = Annotated[StructuringService, Depends(get_structuring_service)]
