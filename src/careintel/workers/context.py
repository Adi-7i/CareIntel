"""
Worker context setup.
"""

import uuid
from collections.abc import Generator
from contextlib import contextmanager

from careintel.core.correlation import _correlation_id_var
from careintel.domain.auth.models import UserContext

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
