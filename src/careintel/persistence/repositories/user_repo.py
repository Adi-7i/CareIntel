"""
User repository.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careintel.domain.auth.models import UserContext
from careintel.persistence.models.user import (
    PermissionORM,
    RoleORM,
    RolePermissionORM,
    UserORM,
    UserRoleORM,
)


class UserRepository:
    """Repository for User data."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserORM | None:
        """Get user by ID without loading roles."""
        return await self.session.get(UserORM, user_id)

    async def get_with_roles(self, user_id: uuid.UUID) -> UserORM | None:
        """Get user by ID, eager loading roles and their permissions."""
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.roles).selectinload(RoleORM.permissions))
            .where(UserORM.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserORM | None:
        """Get user by email (case-insensitive)."""
        stmt = select(UserORM).where(UserORM.email.ilike(email))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_role_by_name_for_update(self, name: str) -> RoleORM | None:
        """Lock and return a role so bootstrap role assignment is serialized."""
        stmt = select(RoleORM).where(RoleORM.name == name).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def role_has_assignment(self, role_id: uuid.UUID) -> bool:
        """Return whether any user is assigned to the supplied role."""
        stmt = select(UserRoleORM.user_id).where(UserRoleORM.role_id == role_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_permissions_by_codes(self, codes: set[str]) -> list[PermissionORM]:
        """Load existing permission definitions by their stable codes."""
        stmt = select(PermissionORM).where(PermissionORM.code.in_(codes))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def ensure_role_permissions(
        self,
        role_id: uuid.UUID,
        permissions: list[PermissionORM],
    ) -> None:
        """Idempotently attach existing permission definitions to a role."""
        permission_ids = {permission.id for permission in permissions}
        if not permission_ids:
            return
        stmt = select(RolePermissionORM.permission_id).where(
            RolePermissionORM.role_id == role_id,
            RolePermissionORM.permission_id.in_(permission_ids),
        )
        result = await self.session.execute(stmt)
        existing_ids = set(result.scalars().all())
        for permission_id in permission_ids - existing_ids:
            self.session.add(RolePermissionORM(role_id=role_id, permission_id=permission_id))
        await self.session.flush()

    async def assign_role(self, assignment: UserRoleORM) -> UserRoleORM:
        """Persist one explicit user-role and facility-scope assignment."""
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def get_role_facilities(self, user_id: uuid.UUID) -> dict[str, uuid.UUID | None]:
        """Return the explicit facility scope attached to each granted role."""
        stmt = (
            select(RoleORM.name, UserRoleORM.facility_id)
            .join(UserRoleORM, UserRoleORM.role_id == RoleORM.id)
            .where(UserRoleORM.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        role_facilities: dict[str, uuid.UUID | None] = {}
        for role_name, facility_id in result.tuples():
            role_facilities[role_name] = facility_id
        return role_facilities

    async def get_user_context(self, user_id: uuid.UUID) -> UserContext | None:
        user = await self.get_with_roles(user_id)
        if user is None:
            return None
        return UserContext(
            id=user.id,
            is_active=user.is_active,
            roles={role.name for role in user.roles},
            permissions={permission.code for role in user.roles for permission in role.permissions},
            role_facilities=await self.get_role_facilities(user.id),
        )

    async def create(self, user: UserORM) -> UserORM:
        """Create a new user."""
        self.session.add(user)
        # Flush to generate ID without committing transaction
        await self.session.flush()
        return user
