"""
Audit repository.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.core.logging import redact_sensitive_data
from careintel.persistence.models.audit import AuditLogORM


class AuditRepository:
    """
    Append-only repository for Audit Logs.
    Intentionally does not implement update() or delete().
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, log_entry: AuditLogORM) -> AuditLogORM:
        """Write an audit record to the database."""
        if log_entry.detail is not None:
            log_entry.detail = redact_sensitive_data(log_entry.detail)
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry

    async def append_security_event(self, log_entry: AuditLogORM) -> AuditLogORM:
        """Persist a security event even when the caller must subsequently fail closed."""
        saved = await self.append(log_entry)
        await self.session.commit()
        return saved
