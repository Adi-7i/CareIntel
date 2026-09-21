"""
v1 API router — aggregates all v1 sub-routers.

Add new feature routers here as modules are built in subsequent steps.
Keep this file as an aggregator only; no handler logic belongs here.
"""

from __future__ import annotations

from fastapi import APIRouter

from careintel.api.v1.auth import router as auth_router
from careintel.api.v1.cases import router as cases_router
from careintel.api.v1.consent import router as consent_router
from careintel.api.v1.escalation import router as escalation_router
from careintel.api.v1.evidence import router as evidence_router
from careintel.api.v1.handoff import router as handoff_router
from careintel.api.v1.health import router as health_router
from careintel.api.v1.processing import router as processing_router
from careintel.api.v1.review import router as review_router
from careintel.api.v1.structuring import router as structuring_router
from careintel.api.v1.tasks import router as tasks_router

router = APIRouter(prefix="/api/v1")

# Phase 1: Core Foundation
router.include_router(health_router.router)
router.include_router(auth_router.router)

# Phase 2: Domain Modeling & Consent
router.include_router(consent_router.router)
router.include_router(cases_router.router)

# Phase 3 & 4: Evidence & Processing
router.include_router(evidence_router.router)
router.include_router(processing_router.router)

# Phase 5: Information Extraction
router.include_router(structuring_router.router)

# Phase 8: Async Workflow Execution
router.include_router(tasks_router.router)

# Phase 9: Human Review & Handoff
router.include_router(review_router.router)
router.include_router(escalation_router.router)
router.include_router(handoff_router.router)
# Future routers added here, e.g.:
# router.include_router(documents_router)
# router.include_router(reviews_router)
