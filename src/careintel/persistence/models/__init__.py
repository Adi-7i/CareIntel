"""
ORM Models aggregator.

Import all ORM models here so that they are registered with the DeclarativeBase metadata.
This ensures Alembic's autogenerate feature detects all tables.
"""

from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.case import (
    CaseORM,
    CaseOutboxORM,
    CaseStateHistoryORM,
    EncounterORM,
)
from careintel.persistence.models.consent import ConsentEventORM, ConsentORM
from careintel.persistence.models.evidence import (
    EvidenceORM,
    EvidenceOutboxORM,
    EvidenceStateHistoryORM,
    TextContentORM,
)
from careintel.persistence.models.processing import (
    ExtractedCandidateORM,
    ExtractionRunORM,
    LanguageResultORM,
    OcrPageORM,
    OcrRegionORM,
    OcrTableCandidateORM,
    ProcessingRunORM,
    TranscriptRunORM,
    TranscriptSegmentORM,
)
from careintel.persistence.models.session import TokenSessionORM
from careintel.persistence.models.user import (
    PermissionORM,
    RoleORM,
    RolePermissionORM,
    UserORM,
    UserRoleORM,
)

__all__ = [
    "AuditLogORM",
    "CaseORM",
    "CaseOutboxORM",
    "CaseStateHistoryORM",
    "ConsentEventORM",
    "ConsentORM",
    "EncounterORM",
    "EvidenceORM",
    "EvidenceOutboxORM",
    "EvidenceStateHistoryORM",
    "ExtractedCandidateORM",
    "ExtractionRunORM",
    "LanguageResultORM",
    "OcrPageORM",
    "OcrRegionORM",
    "OcrTableCandidateORM",
    "PermissionORM",
    # Processing
    "ProcessingRunORM",
    "RoleORM",
    "RolePermissionORM",
    "TextContentORM",
    "TokenSessionORM",
    "TranscriptRunORM",
    "TranscriptSegmentORM",
    "UserORM",
    "UserRoleORM",
]
