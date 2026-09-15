"""
Token Session repository.
"""

from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.session import TokenSessionORM


class SessionRepository:
    """Repository for Token Sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, token_session: TokenSessionORM) -> TokenSessionORM:
        """Record a new issued token session."""
        self.session.add(token_session)
        await self.session.flush()
        return token_session

    async def get_by_jti(self, jti: str) -> TokenSessionORM | None:
        """Find a session by its unique JWT ID."""
        stmt = select(TokenSessionORM).where(TokenSessionORM.jti == jti)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, jti: str, reason: str | None = None) -> bool:
        """
        Revoke an active session.
        Returns True if revoked, False if not found or already revoked.
        """
        session_orm = await self.get_by_jti(jti)
        if not session_orm or session_orm.revoked_at is not None:
            return False

        # Use UTC timestamp since our app expects TIMESTAMPTZ.
        session_orm.revoked_at = datetime.datetime.now(datetime.UTC)
        session_orm.revoked_reason = reason
        await self.session.flush()
        return True

    async def is_revoked(self, jti: str) -> bool:
        """Check if a session is revoked or missing."""
        session_orm = await self.get_by_jti(jti)
        if not session_orm:
            return True  # If it doesn't exist, treat as revoked/invalid
        return session_orm.revoked_at is not None
