"""
Shared FastAPI dependency providers for the API layer.

All dependencies follow FastAPI's Depends() pattern.
Route handlers declare what they need; this module wires the concrete implementations.

Rules:
- Dependency providers must NOT contain business logic.
- Database sessions are created here and injected; route handlers never access
  the session factory or engine directly.
- Settings are injected via Depends; route handlers never call get_settings() directly.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated, Any, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.auth.auth_service import AuthService
from careintel.application.auth.password_hasher import PasswordHasher
from careintel.application.auth.permission_service import PermissionService
from careintel.application.auth.token_service import JWTService
from careintel.application.case.case_service import CaseService
from careintel.application.evidence.evidence_service import EvidenceService
from careintel.application.evidence.file_validator import FileValidator
from careintel.application.processing.document_processor import DocumentProcessor
from careintel.application.processing.extraction_processor import ExtractionProcessor
from careintel.application.processing.language_processor import LanguageProcessor
from careintel.application.processing.processing_service import ProcessingService
from careintel.application.processing.speech_processor import SpeechProcessor
from careintel.core.config import Settings, get_settings
from careintel.core.database import get_async_session
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.infrastructure.language.port import LanguageProvider
from careintel.infrastructure.ocr.port import OcrProvider
from careintel.infrastructure.scanner.port import ContentScannerPort
from careintel.infrastructure.storage.port import BlobStoragePort
from careintel.infrastructure.stt.port import SpeechProvider
from careintel.infrastructure.translation.port import TranslationProvider
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.case_history_repo import CaseHistoryRepository
from careintel.persistence.repositories.case_outbox_repo import CaseOutboxRepository
from careintel.persistence.repositories.case_repo import CaseRepository
from careintel.persistence.repositories.evidence_history_repo import EvidenceHistoryRepository
from careintel.persistence.repositories.evidence_outbox_repo import EvidenceOutboxRepository
from careintel.persistence.repositories.evidence_repo import EvidenceRepository
from careintel.persistence.repositories.processing_repo import ProcessingRepository
from careintel.persistence.repositories.session_repo import SessionRepository
from careintel.persistence.repositories.text_content_repo import TextContentRepository
from careintel.persistence.repositories.user_repo import UserRepository

# Using FastAPI's built-in HTTPBearer for token extraction (swagger integration)
token_bearer = HTTPBearer(auto_error=False)

# ── Settings ──────────────────────────────────────────────────────────────────


def _settings_provider() -> Settings:
    """Inject application settings."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(_settings_provider)]


# ── Database Session ───────────────────────────────────────────────────────────


async def _db_session_provider(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Inject a request-scoped async database session.

    The session factory is stored on app.state during startup.
    Commits on clean exit; rolls back and closes on error.
    """
    session_factory = request.app.state.db_session_factory
    async with get_async_session(session_factory) as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(_db_session_provider)]


# ── Authentication & Authorization ─────────────────────────────────────────────


from careintel.application.auth.consent_service import ConsentService
from careintel.persistence.repositories.consent_repo import ConsentRepository

def get_consent_service(session: DbSessionDep) -> ConsentService:
    return ConsentService(
        consent_repo=ConsentRepository(session),
        audit_repo=AuditRepository(session),
    )


def get_auth_service(
    session: DbSessionDep,
    settings: SettingsDep,
) -> AuthService:
    """Provide the AuthService."""
    return AuthService(
        user_repo=UserRepository(session),
        session_repo=SessionRepository(session),
        audit_repo=AuditRepository(session),
        token_service=JWTService(settings),
        hasher=PasswordHasher(),
    )


async def get_optional_user(
    token_cred: Annotated[HTTPAuthorizationCredentials | None, Depends(token_bearer)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserContext | None:
    """Extract and validate the current user from token, if provided."""
    if not token_cred:
        return None
    try:
        return await auth_service.get_current_user(token_cred.credentials)
    except Exception:
        # If optional, we ignore auth errors
        return None


async def get_current_user(
    token_cred: Annotated[HTTPAuthorizationCredentials | None, Depends(token_bearer)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserContext:
    """Extract and validate the current user from token. Raises 401 if missing/invalid."""
    from careintel.core.errors import AuthError

    if not token_cred:
        raise AuthError("Authentication credentials are required.")

    return await auth_service.get_current_user(token_cred.credentials)


async def get_raw_token(
    token_cred: Annotated[HTTPAuthorizationCredentials | None, Depends(token_bearer)],
) -> str:
    """Extract the raw token string from the request."""
    from careintel.core.errors import AuthError

    if not token_cred:
        raise AuthError("Authentication credentials are required.")
    return token_cred.credentials


CurrentUserDep = Annotated[UserContext, Depends(get_current_user)]
OptionalUserDep = Annotated[UserContext | None, Depends(get_optional_user)]
RawTokenDep = Annotated[str, Depends(get_raw_token)]


def require_permission(permission: Permission | str) -> Any:
    """
    Dependency factory to enforce RBAC permissions.
    """

    async def _require_permission(user: CurrentUserDep) -> None:
        PermissionService.check(actor=user, action=permission)

    return Depends(_require_permission)


# ── Case & Evidence Services ──────────────────────────────────────────────────


def get_case_service(
    session: DbSessionDep,
) -> CaseService:
    return CaseService(
        case_repo=CaseRepository(session),
        history_repo=CaseHistoryRepository(session),
        outbox_repo=CaseOutboxRepository(session),
        audit_repo=AuditRepository(session),
    )


def get_blob_provider(request: Request) -> BlobStoragePort:
    """Get the blob storage provider initialized in app lifespan."""
    return cast(BlobStoragePort, request.app.state.blob_provider)


def get_content_scanner(request: Request) -> ContentScannerPort:
    """Get the content scanner initialized in app lifespan."""
    return cast(ContentScannerPort, request.app.state.content_scanner)


def get_evidence_service(
    session: DbSessionDep,
    settings: SettingsDep,
    case_service: Annotated[CaseService, Depends(get_case_service)],
    blob_provider: Annotated[BlobStoragePort, Depends(get_blob_provider)],
    scanner: Annotated[ContentScannerPort, Depends(get_content_scanner)],
) -> EvidenceService:
    """Construct EvidenceService with all required repositories."""
    return EvidenceService(
        case_repo=CaseRepository(session),
        evidence_repo=EvidenceRepository(session),
        text_repo=TextContentRepository(session),
        history_repo=EvidenceHistoryRepository(session),
        outbox_repo=EvidenceOutboxRepository(session),
        audit_repo=AuditRepository(session),
        case_service=case_service,
        blob_provider=blob_provider,
        scanner=scanner,
        file_validator=FileValidator(
            allowed_extensions=settings.evidence_allowed_extensions,
            max_size_bytes=settings.evidence_max_file_size_bytes,
        ),
        sas_ttl_minutes=settings.evidence_sas_ttl_minutes,
    )


# ── Processing Services ────────────────────────────────────────────────────────


def get_ocr_provider(request: Request) -> OcrProvider:
    return cast(OcrProvider, request.app.state.ocr_provider)


def get_speech_provider(request: Request) -> SpeechProvider:
    return cast(SpeechProvider, request.app.state.speech_provider)


def get_language_provider(request: Request) -> LanguageProvider:
    return cast(LanguageProvider, request.app.state.language_provider)


def get_translation_provider(request: Request) -> TranslationProvider:
    return cast(TranslationProvider, request.app.state.translation_provider)


def get_processing_service(
    request: Request,
    session: DbSessionDep,
    settings: SettingsDep,
    blob_provider: Annotated[BlobStoragePort, Depends(get_blob_provider)],
    ocr_provider: Annotated[OcrProvider, Depends(get_ocr_provider)],
    speech_provider: Annotated[SpeechProvider, Depends(get_speech_provider)],
    language_provider: Annotated[LanguageProvider, Depends(get_language_provider)],
    translation_provider: Annotated[TranslationProvider, Depends(get_translation_provider)],
) -> ProcessingService:
    evidence_repo = EvidenceRepository(session)
    processing_repo = ProcessingRepository(session)
    outbox_repo = EvidenceOutboxRepository(session)

    doc_processor = DocumentProcessor(
        settings=settings,
        evidence_repo=evidence_repo,
        processing_repo=processing_repo,
        outbox_repo=outbox_repo,
        blob_storage=blob_provider,
        ocr_provider=ocr_provider,
    )

    speech_processor = SpeechProcessor(
        settings=settings,
        evidence_repo=evidence_repo,
        processing_repo=processing_repo,
        outbox_repo=outbox_repo,
        blob_storage=blob_provider,
        speech_provider=speech_provider,
    )

    lang_processor = LanguageProcessor(
        settings=settings,
        evidence_repo=evidence_repo,
        processing_repo=processing_repo,
        outbox_repo=outbox_repo,
        language_provider=language_provider,
        translation_provider=translation_provider,
    )

    ext_processor = ExtractionProcessor(
        settings=settings,
        evidence_repo=evidence_repo,
        processing_repo=processing_repo,
        outbox_repo=outbox_repo,
        extraction_provider=request.app.state.extraction_provider,  # or get_extraction_provider
    )

    return ProcessingService(
        document_processor=doc_processor,
        speech_processor=speech_processor,
        language_processor=lang_processor,
        extraction_processor=ext_processor,
    )
