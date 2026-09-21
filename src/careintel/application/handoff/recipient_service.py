"""
Recipient Service.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from careintel.core.errors import AuthorizationError, NotFoundError
from careintel.domain.auth.models import UserContext
from careintel.domain.auth.permissions import Permission
from careintel.domain.auth.policy import AuthorizationPolicy
from careintel.persistence.models.handoff import RecipientORM
from careintel.persistence.repositories.handoff_repo import HandoffRepository


class RecipientService:
    """Manages the configurable recipients for handoffs."""

    def __init__(self, handoff_repo: HandoffRepository) -> None:
        self.handoff_repo = handoff_repo

    async def list_active_recipients(self, actor: UserContext) -> Sequence[RecipientORM]:
        if not AuthorizationPolicy.evaluate(actor, Permission.HANDOFF_READ):
            raise AuthorizationError("Actor not authorized to read recipients.")
        return await self.handoff_repo.list_active_recipients()

    async def get_recipient(self, recipient_id: uuid.UUID, actor: UserContext) -> RecipientORM:
        if not AuthorizationPolicy.evaluate(actor, Permission.HANDOFF_READ):
             raise AuthorizationError("Actor not authorized to read recipients.")
        
        recipient = await self.handoff_repo.get_recipient(recipient_id)
        if not recipient:
             raise NotFoundError("Recipient not found.")
        return recipient
