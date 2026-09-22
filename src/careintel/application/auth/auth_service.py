"""
Authentication application service.
"""

from __future__ import annotations

import datetime
import uuid

from careintel.application.auth.password_hasher import PasswordHasher
from careintel.application.auth.token_service import JWTService
from careintel.core.errors import AuthError
from careintel.domain.audit.events import AuditEventType
from careintel.domain.auth.models import UserContext
from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.session import TokenSessionORM
from careintel.persistence.repositories.audit_repo import AuditRepository
from careintel.persistence.repositories.session_repo import SessionRepository
from careintel.persistence.repositories.user_repo import UserRepository


class AuthService:
    """Orchestrates authentication use cases."""

    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        audit_repo: AuditRepository,
        token_service: JWTService,
        hasher: PasswordHasher,
    ) -> None:
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.audit_repo = audit_repo
        self.token_service = token_service
        self.hasher = hasher

    async def login(
        self, email: str, password: str, correlation_id: str
    ) -> tuple[str, UserContext]:
        """
        Authenticate user and issue a JWT.
        """
        user = await self.user_repo.get_by_email(email)

        if not user or not self.hasher.verify(password, user.password_hash):
            await self.audit_repo.append(
                AuditLogORM(
                    event_type=AuditEventType.LOGIN_FAILURE,
                    actor_id=user.id if user else None,
                    correlation_id=correlation_id,
                    outcome="FAILURE",
                )
            )
            raise AuthError("Invalid email or password.")

        if not user.is_active:
            await self.audit_repo.append(
                AuditLogORM(
                    event_type=AuditEventType.LOGIN_FAILURE,
                    actor_id=user.id,
                    correlation_id=correlation_id,
                    outcome="DENIED",
                    detail={"reason": "inactive_account"},
                )
            )
            raise AuthError("Invalid email or password.")

        # Create session record
        session_id = uuid.uuid4()
        now = datetime.datetime.now(datetime.UTC)
        expires = now + datetime.timedelta(minutes=self.token_service.ttl_minutes)

        token = self.token_service.issue_token(user.id, session_id)
        claims = self.token_service.validate_token(token)

        token_session = TokenSessionORM(
            id=session_id,
            user_id=user.id,
            jti=claims.jti,
            issued_at=claims.iat,
            expires_at=expires,
        )
        await self.session_repo.create(token_session)

        # Audit success
        await self.audit_repo.append(
            AuditLogORM(
                event_type=AuditEventType.LOGIN_SUCCESS,
                actor_id=user.id,
                correlation_id=correlation_id,
                outcome="SUCCESS",
            )
        )

        user_with_roles = await self.user_repo.get_with_roles(user.id)
        assert user_with_roles is not None

        # For login, we just return a basic UserContext. The detailed one with permissions
        # is usually loaded per request in get_current_user.
        user_context = UserContext(
            id=user.id,
            is_active=user.is_active,
        )
        return token, user_context

    async def get_current_user(self, token: str) -> UserContext:
        """
        Validate token and return current UserContext with permissions.
        """
        claims = self.token_service.validate_token(token)

        if await self.session_repo.is_revoked(claims.jti):
            raise AuthError("Token has been revoked.")

        user = await self.user_repo.get_with_roles(claims.sub)
        if not user or not user.is_active:
            raise AuthError("User is inactive or deleted.")

        # We need the user's roles and permissions.
        roles = {role.name for role in user.roles}
        permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                permissions.add(perm.code)

        # Facility grants live on the user-role association, not RoleORM.  Load
        # them explicitly so object-level authorization cannot mistake a missing
        # mapping for a system-wide role.
        role_facilities = await self.user_repo.get_role_facilities(user.id)

        return UserContext(
            id=user.id,
            is_active=user.is_active,
            roles=roles,
            permissions=permissions,
            role_facilities=role_facilities,
        )

    async def logout(self, token: str, correlation_id: str) -> None:
        """
        Revoke the current token.
        """
        try:
            claims = self.token_service.validate_token(token)
        except AuthError:
            return  # Already invalid/expired

        revoked = await self.session_repo.revoke(claims.jti, reason="logout")
        if revoked:
            await self.audit_repo.append(
                AuditLogORM(
                    event_type=AuditEventType.LOGOUT,
                    actor_id=claims.sub,
                    correlation_id=correlation_id,
                    outcome="SUCCESS",
                )
            )
