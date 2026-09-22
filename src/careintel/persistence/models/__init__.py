"""
ORM Models aggregator.

Import all ORM models here so that they are registered with the DeclarativeBase metadata.
This ensures Alembic's autogenerate feature detects all tables.
"""

from careintel.persistence.models.ai import AIDraftORM, AIRunORM, PolicyDecisionORM
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
from careintel.persistence.models.knowledge import (
    ChunkEmbeddingORM,
    EmbeddingVersionORM,
    KnowledgeChunkORM,
    KnowledgeSourceORM,
    KnowledgeVersionORM,
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
from careintel.persistence.models.retrieval import RetrievalCandidateORM, RetrievalRunORM
from careintel.persistence.models.session import TokenSessionORM
from careintel.persistence.models.structuring import (
    ChecklistPolicyVersionORM,
    ClarificationQuestionORM,
    ConflictCandidateLinkORM,
    ConflictRecordORM,
    MissingInfoItemORM,
    StructuringRunORM,
    TimelineEventORM,
)
from careintel.persistence.models.user import (
    PermissionORM,
    RoleORM,
    RolePermissionORM,
    UserORM,
    UserRoleORM,
)
from careintel.persistence.models.workflow import AsyncTaskORM

__all__ = [
    "AIDraftORM",
    "AIRunORM",
    "AsyncTaskORM",
    "AuditLogORM",
    "CaseORM",
    "CaseOutboxORM",
    "CaseStateHistoryORM",
    "ChecklistPolicyVersionORM",
    "ChunkEmbeddingORM",
    "ClarificationQuestionORM",
    "ConflictCandidateLinkORM",
    "ConflictRecordORM",
    "ConsentEventORM",
    "ConsentORM",
    "EmbeddingVersionORM",
    "EncounterORM",
    "EvidenceORM",
    "EvidenceOutboxORM",
    "EvidenceStateHistoryORM",
    "ExtractedCandidateORM",
    "ExtractionRunORM",
    "KnowledgeChunkORM",
    "KnowledgeSourceORM",
    "KnowledgeVersionORM",
    "LanguageResultORM",
    "MissingInfoItemORM",
    "OcrPageORM",
    "OcrRegionORM",
    "OcrTableCandidateORM",
    "PermissionORM",
    "PolicyDecisionORM",
    "ProcessingRunORM",
    "RetrievalCandidateORM",
    "RetrievalRunORM",
    "RoleORM",
    "RolePermissionORM",
    "StructuringRunORM",
    "TextContentORM",
    "TimelineEventORM",
    "TokenSessionORM",
    "TranscriptRunORM",
    "TranscriptSegmentORM",
    "UserORM",
    "UserRoleORM",
]
