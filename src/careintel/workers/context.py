"""
Worker context setup.
"""

import uuid
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from careintel.core.correlation import _correlation_id_var
from careintel.domain.auth.models import UserContext
from careintel.persistence.repositories.user_repo import UserRepository

# System worker actor UUID (reserved).
# In a real migration, this UUID would be seeded into the users table.
SYSTEM_WORKER_ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@contextmanager
def setup_worker_context(correlation_id: str, actor_id: str) -> Generator[UserContext, None, None]:
    """
    Set up the correlation ID and actor context for the worker.
    Yields a UserContext representing the system worker.
    """
    token = _correlation_id_var.set(correlation_id)
    try:
        # Workers execute as a special SYSTEM_WORKER actor, but we may want
        # to record the original human actor_id in the audit logs.
        # For authorization, we yield the system worker context.
        worker_context = UserContext(
            id=SYSTEM_WORKER_ACTOR_ID,
            is_active=True,
            roles={"system_worker"},
            permissions=set(),
            role_facilities={},
        )
        yield worker_context
    finally:
        _correlation_id_var.reset(token)


async def load_worker_actor(session: AsyncSession, actor_id: uuid.UUID) -> UserContext:
    """Hydrate the initiating human actor from current authoritative RBAC state."""
    repo = UserRepository(session)
    user = await repo.get_with_roles(actor_id)
    if user is None or not user.is_active:
        raise PermissionError("Task actor is inactive or unavailable.")
    roles = {role.name for role in user.roles}
    permissions = {permission.code for role in user.roles for permission in role.permissions}
    return UserContext(
        id=user.id,
        is_active=user.is_active,
        roles=roles,
        permissions=permissions,
        role_facilities=await repo.get_role_facilities(user.id),
    )
