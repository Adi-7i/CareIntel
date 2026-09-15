"""
Audit repository.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

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
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry
