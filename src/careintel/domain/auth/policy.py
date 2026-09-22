"""
Authorization policy.
"""

from __future__ import annotations

import uuid

from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission


class AuthorizationPolicy:
    """
    Central authorization policy evaluator.
    Follows a Deny-by-Default model.
    """

    @staticmethod
    def evaluate(
        actor: UserContext,
        action: str | Permission,
        resource_type: str | None = None,
        facility_scope: uuid.UUID | None = None,
        resource_state: str | None = None,
        purpose: str | None = None,
    ) -> bool:
        """
        Evaluate if the actor is permitted to perform the action.

        Returns True if granted, False if denied.
        """
        if not actor.is_active:
            return False

        action_str = str(action)
        if action_str not in actor.permissions:
            return False

        # Facility scope check:
        # If the resource belongs to a specific facility, we check if the user
        # has the required permission in a role that grants access to that facility
        # or if they have a system-wide role (facility_id is None).
        if facility_scope is not None:
            has_facility_access = False
            for role_name in actor.roles:
                # A missing mapping is not a system-wide grant.  System-wide access
                # must be represented explicitly by a role mapping whose value is
                # None; otherwise an incompletely hydrated UserContext would bypass
                # the facility boundary.
                if role_name not in actor.role_facilities:
                    continue
                role_facility = actor.role_facilities.get(role_name)

                if role_facility is None or role_facility == facility_scope:
                    has_facility_access = True
                    break

            if not has_facility_access:
                return False

        # Future extensions for object ownership, resource_state, etc. go here.

        return True
