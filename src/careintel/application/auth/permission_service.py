"""
Permission application service.
"""

from __future__ import annotations

import uuid

from careintel.core.errors import AuthorizationError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.policy import AuthorizationPolicy


class PermissionService:
    """Service to evaluate authorization rules."""

    @staticmethod
    def check(
        actor: UserContext,
        action: str,
        resource_type: str | None = None,
        facility_scope: uuid.UUID | None = None,
    ) -> None:
        """
        Evaluate if actor can perform action. Raises AuthorizationError on deny.
        """
        granted = AuthorizationPolicy.evaluate(
            actor=actor,
            action=action,
            resource_type=resource_type,
            facility_scope=facility_scope,
        )
        if not granted:
            raise AuthorizationError()
