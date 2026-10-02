# ──────────────────────────────────────────────────────────────────────────────
# CareIntel — Production Dockerfile
#
# Build strategy:
#   Stage 1 (builder): Install uv, resolve and pre-install all Python
#                      dependencies into a hermetic virtual environment.
#   Stage 2 (runtime): Copy only the venv and application source.
#                      Run as a non-root user with no build tooling present.
#
# Native OS dependency:
#   libmagic1 is required by python-magic (used for upload MIME detection).
#   It must be present in the runtime image; it is not a Python package.
#
# Secrets policy:
#   No secrets, credentials, .env files, or private keys are copied into
#   any image layer. All runtime secrets must be injected at container
#   start-up through the deployment environment or a secret manager.
#
# Usage:
#   docker build -t careintel:latest .
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

# Install uv from the official image — the canonical dependency manager.
COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /usr/local/bin/

WORKDIR /build

# Copy only the files uv needs to resolve dependencies. This layer is cached
# as long as pyproject.toml and uv.lock do not change.
# Copy only the files uv needs to resolve dependencies. This layer is cached
# as long as pyproject.toml and uv.lock do not change.
# README.md is required by hatchling to validate the package metadata declared
# in pyproject.toml (readme = "README.md"). It is not copied to the runtime stage.
COPY pyproject.toml uv.lock README.md ./


# Install all production dependencies into a virtual environment, reproducibly
# from the committed lock file. --no-dev excludes test/lint tooling.
# --no-install-project defers editable project install so this layer is
# reusable across source-only changes.
RUN uv sync \
        --frozen \
        --no-dev \
        --no-install-project \
    && uv cache clean

# Copy application source and install the package itself.
COPY src/ ./src/

RUN uv sync \
        --frozen \
        --no-dev

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

# libmagic1 is required by python-magic for upload MIME type detection.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Non-root runtime user — no home directory, no shell.
RUN groupadd --gid 1001 appgroup \
    && useradd \
        --uid 1001 \
        --gid appgroup \
        --no-create-home \
        --shell /sbin/nologin \
        appuser

# Working directory must match the repository root because relative paths
# such as config/checklists/ and migrations/ are resolved from here.
WORKDIR /app

# Virtual environment from the builder stage.
COPY --from=builder --chown=appuser:appgroup /build/.venv /app/.venv

# Application source.
COPY --chown=appuser:appgroup src/ ./src/

# Runtime-required repository artifacts:
#   config/checklists/ - structuring policy files read at request time
#   migrations/        - Alembic migration scripts
#   alembic.ini        - Alembic configuration (script_location = migrations)
#   scripts/           - Operational scripts (bootstrap_admin, verify_infra)
COPY --chown=appuser:appgroup config/ ./config/
COPY --chown=appuser:appgroup migrations/ ./migrations/
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup scripts/ ./scripts/

# Python runtime flags.
# PYTHONUNBUFFERED=1         - unbuffered output required for log drivers.
# PYTHONDONTWRITEBYTECODE=1  - no .pyc files in image layers.
# PYTHONPATH=/app/src        - ensures careintel package is importable.
# PATH                       - venv bin takes precedence over system python.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

USER appuser

# Only the application port is exposed. No admin, metrics, or debug ports.
EXPOSE 8000

# Default command: FastAPI API server.
# Overridden by compose.yaml for the worker and outbox services.
# --workers 1: one process per container; scale via replicas, not fork.
# Do NOT add --reload in production.
CMD ["uvicorn", "careintel.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
