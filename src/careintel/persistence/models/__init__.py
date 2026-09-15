"""
ORM Models aggregator.

Import all ORM models here so that they are registered with the DeclarativeBase metadata.
This ensures Alembic's autogenerate feature detects all tables.
"""

from careintel.persistence.models.audit import AuditLogORM
from careintel.persistence.models.consent import ConsentEventORM, ConsentORM
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
    "ConsentEventORM",
    "ConsentORM",
    "PermissionORM",
    "RoleORM",
    "RolePermissionORM",
    "TokenSessionORM",
    "UserORM",
    "UserRoleORM",
]
