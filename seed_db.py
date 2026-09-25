"""
Database seed script for CareIntel demo environment.
Populates standard roles, permissions, and demo users.
"""

import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.application.auth.password_hasher import PasswordHasher
from careintel.core.config import get_settings
from careintel.core.database import build_engine, build_session_factory, dispose_engine
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.roles import Role
from careintel.persistence.models.user import (
    PermissionORM,
    RoleORM,
    RolePermissionORM,
    UserORM,
    UserRoleORM,
)


async def seed() -> None:
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    hasher = PasswordHasher()

    async with session_factory() as session:
        print("[*] Seeding permissions...")
        perm_map: dict[str, uuid.UUID] = {}
        for perm in Permission:
            stmt = select(PermissionORM).where(PermissionORM.code == perm.value)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                new_perm = PermissionORM(id=uuid.uuid4(), code=perm.value)
                session.add(new_perm)
                perm_map[perm.value] = new_perm.id
            else:
                perm_map[perm.value] = existing.id

        await session.flush()

        print("[*] Seeding roles...")
        role_map: dict[str, uuid.UUID] = {}
        for r in Role:
            stmt = select(RoleORM).where(RoleORM.name == r.value)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                new_role = RoleORM(id=uuid.uuid4(), name=r.value)
                session.add(new_role)
                role_map[r.value] = new_role.id
            else:
                role_map[r.value] = existing.id

        await session.flush()

        # Link all permissions to admin and doctor
        for role_name, role_id in role_map.items():
            for perm_code, perm_id in perm_map.items():
                stmt = select(RolePermissionORM).where(
                    RolePermissionORM.role_id == role_id,
                    RolePermissionORM.permission_id == perm_id,
                )
                res = await session.execute(stmt)
                if not res.scalar_one_or_none():
                    session.add(RolePermissionORM(role_id=role_id, permission_id=perm_id))

        await session.flush()

        print("[*] Seeding demo users...")
        demo_users = [
            ("doctor@careintel.local", "Dr. Sharma (Medical Officer)", "demo123", "doctor"),
            ("nurse@careintel.local", "Sunita B. (Triage Nurse)", "demo123", "nurse"),
            ("cho@careintel.local", "Ramesh Sahoo (CHO)", "demo123", "health_worker"),
            ("admin@careintel.local", "System Administrator", "demo123", "admin"),
        ]

        for email, display_name, password, role_name in demo_users:
            stmt = select(UserORM).where(UserORM.email == email)
            res = await session.execute(stmt)
            existing_user = res.scalar_one_or_none()
            if not existing_user:
                user_id = uuid.uuid4()
                new_user = UserORM(
                    id=user_id,
                    email=email,
                    display_name=display_name,
                    password_hash=hasher.hash(password),
                    is_active=True,
                    is_verified=True,
                )
                session.add(new_user)
                await session.flush()

                role_id = role_map.get(role_name)
                if role_id:
                    session.add(UserRoleORM(user_id=user_id, role_id=role_id))
                print(f"  + Created user {email} (password: {password})")
            else:
                print(f"  = User {email} already exists")

        await session.commit()
        print("[SUCCESS] Database seeding completed successfully!")

    await dispose_engine(engine)


if __name__ == "__main__":
    asyncio.run(seed())
