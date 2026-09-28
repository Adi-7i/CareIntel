"""
User repository.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careintel.domain.auth.models import UserContext
from careintel.persistence.models.user import RoleORM, UserORM, UserRoleORM


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
