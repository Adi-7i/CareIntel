"""
Handoff and Referral repositories.
"""

import uuid
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from careintel.persistence.models.handoff import HandoffORM, RecipientORM, ReferralPackageORM


class HandoffRepository:
    """Repository for handoffs and referrals."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Recipients ───────────────────────────────────────────────────────────

    async def get_recipient(self, recipient_id: uuid.UUID) -> RecipientORM | None:
        return await self.session.get(RecipientORM, recipient_id)

    async def list_active_recipients(self) -> Sequence[RecipientORM]:
        stmt = select(RecipientORM).where(RecipientORM.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ── Referral Packages ────────────────────────────────────────────────────

    async def create_referral_package(self, package: ReferralPackageORM) -> ReferralPackageORM:
        self.session.add(package)
        await self.session.flush()
        return package

    async def get_referral_package(self, package_id: uuid.UUID) -> ReferralPackageORM | None:
        return await self.session.get(ReferralPackageORM, package_id)

    async def get_packages_for_case(self, case_id: uuid.UUID) -> Sequence[ReferralPackageORM]:
        stmt = (
            select(ReferralPackageORM)
            .where(ReferralPackageORM.case_id == case_id)
            .order_by(ReferralPackageORM.version.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_package_for_case(self, case_id: uuid.UUID) -> ReferralPackageORM | None:
        stmt = (
            select(ReferralPackageORM)
            .where(ReferralPackageORM.case_id == case_id)
            .order_by(ReferralPackageORM.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Handoffs ─────────────────────────────────────────────────────────────

    async def create_handoff(self, handoff: HandoffORM) -> HandoffORM:
        self.session.add(handoff)
        await self.session.flush()
        return handoff

    async def get_handoff(self, handoff_id: uuid.UUID) -> HandoffORM | None:
        return await self.session.get(HandoffORM, handoff_id)

    async def get_handoff_for_update(
        self, handoff_id: uuid.UUID, expected_version: int | None = None
    ) -> HandoffORM | None:
        stmt = select(HandoffORM).where(HandoffORM.id == handoff_id).with_for_update()
        if expected_version is not None:
            stmt = stmt.where(HandoffORM.version == expected_version)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_handoffs_for_case(self, case_id: uuid.UUID) -> Sequence[HandoffORM]:
        stmt = (
            select(HandoffORM)
            .where(HandoffORM.case_id == case_id)
            .order_by(HandoffORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
