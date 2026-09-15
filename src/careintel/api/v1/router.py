"""
v1 API router — aggregates all v1 sub-routers.

Add new feature routers here as modules are built in subsequent steps.
Keep this file as an aggregator only; no handler logic belongs here.
"""

from __future__ import annotations

from fastapi import APIRouter

from careintel.api.v1.health.router import router as health_router

router = APIRouter(prefix="/api/v1")

# ── Feature sub-routers ──────────────────────────────────────────────────────
router.include_router(health_router)

# Future routers added here, e.g.:
# router.include_router(documents_router)
# router.include_router(reviews_router)
