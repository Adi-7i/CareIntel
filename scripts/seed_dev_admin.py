"""
Seed a development ADMIN account.
Do not run in production.
"""

import asyncio
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# We need the CareIntel models in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from careintel.application.auth.password_hasher import PasswordHasher
from careintel.core.config import get_settings
from careintel.persistence.models.user import RoleORM, UserORM, UserRoleORM


async def main() -> None:
    settings = get_settings()
    if settings.app_env.value == "production":
        print("ERROR: Cannot run seed script in production.")
        sys.exit(1)

    email = os.getenv("SEED_ADMIN_EMAIL")
    password = os.getenv("SEED_ADMIN_PASSWORD")

    if not email or not password:
        print("ERROR: SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD must be set.")
        sys.exit(1)

    hasher = PasswordHasher()
    hashed_password = hasher.hash(password)

    engine = create_async_engine(settings.database_url_safe(), echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        # Check if user exists
        stmt = select(UserORM).where(UserORM.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            print(f"Admin user {email} already exists. Updating password...")
            user.password_hash = hashed_password
        else:
            print(f"Creating new admin user: {email}")
            user = UserORM(
                email=email,
                display_name="System Admin",
                password_hash=hashed_password,
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            await session.flush()

        # Find the ADMIN role
        role_stmt = select(RoleORM).where(RoleORM.name == "admin")
        role_result = await session.execute(role_stmt)
        admin_role = role_result.scalar_one_or_none()

        if not admin_role:
            print("ERROR: 'admin' role not found in the database. Have you run the migrations?")
            sys.exit(1)

        # Ensure user has ADMIN role
        user_role_stmt = select(UserRoleORM).where(
            UserRoleORM.user_id == user.id, UserRoleORM.role_id == admin_role.id
        )
        ur_result = await session.execute(user_role_stmt)
        ur = ur_result.scalar_one_or_none()

        if not ur:
            print("Granting ADMIN role to user...")
            new_ur = UserRoleORM(
                user_id=user.id,
                role_id=admin_role.id,
            )
            session.add(new_ur)

        await session.commit()
        print("Seed completed successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
