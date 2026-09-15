"""
Domain layer — pure Python, zero external framework dependencies.

Rules (enforced by architecture tests):
- No imports from fastapi, sqlalchemy, alembic, or any HTTP/persistence library.
- Domain models, value objects, and domain services live here.
- Domain errors are defined in careintel.core.errors (shared infrastructure).

This package is intentionally empty in STEP 1.
Business domain models will be added in subsequent steps.
"""
