# CareIntel — Backend

> Non-diagnostic healthcare information and reviewer-workflow system.  
> Keeps qualified human review as the authority. Uses synthetic/public sample data only.

---

## Quick Start

### Prerequisites

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/) (package manager)
- PostgreSQL (external instance — see configuration below)

### 1. Install dependencies

```bash
uv sync --all-extras
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL and SECRET_KEY
```

Minimum required variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:port/dbname` |
| `SECRET_KEY` | Long random string (use `openssl rand -hex 32`) |

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the development server

```bash
uv run uvicorn careintel.main:app --reload --host 127.0.0.1 --port 8000
```

API docs available at: http://127.0.0.1:8000/api/docs

---

## Code Quality

All commands run from the project root:

```bash
# Format (in-place)
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run mypy

# Run all tests (unit + API, no live DB needed)
uv run pytest

# Run with coverage
uv run pytest --cov

# Run integration tests (requires live DATABASE_URL)
uv run pytest tests/integration/ -m integration -v
```

---

## Project Structure

```
src/careintel/
├── main.py              # Thin composition root (app factory)
├── core/
│   ├── config.py        # Typed settings (Pydantic Settings)
│   ├── database.py      # Async SQLAlchemy engine + session management
│   ├── logging.py       # Structured JSON logging + sensitive-data filter
│   ├── correlation.py   # Request/correlation ID middleware
│   └── errors.py        # Global error contract + exception hierarchy
├── api/
│   ├── deps.py          # FastAPI dependency providers
│   └── v1/
│       ├── router.py    # v1 route aggregator
│       └── health/      # /api/v1/health/live + /api/v1/health/ready
└── domain/              # Pure domain layer (no framework dependencies)

migrations/              # Alembic migration scripts
tests/
├── unit/                # Fast, no external dependencies
├── api/                 # ASGI-level tests (no live DB)
└── integration/         # Requires live PostgreSQL
```

---

## Architecture Principles

### Layer Rules (enforced by tests)
- **Domain** → no FastAPI, SQLAlchemy, or external framework imports
- **Core** → Pydantic + stdlib only (no FastAPI in config/logging/correlation)
- **API** → never accesses persistence implementations directly
- **No LangGraph** — future orchestration uses Celery + Redis Streams
- **No Docker** — deferred to final hardening phase

### Error Contract
All API errors return:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource was not found.",
    "correlation_id": "01J..."
  }
}
```

### Correlation IDs
Every request gets an `X-Correlation-ID` header (ULID-based, time-sortable).  
Callers can supply their own; the server echoes it back.

### Security
- Secrets only from environment variables — never hardcoded
- Sensitive fields redacted from logs (`password`, `token`, `authorization`, etc.)
- Request body is never logged
- Error responses strip internal details and stack traces

---

## Health Endpoints

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `GET /api/v1/health/live` | Liveness probe | Always 200 if process is alive |
| `GET /api/v1/health/ready` | Readiness probe | 200/503 based on DB reachability |

---

## Migrations

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Create a new migration
uv run alembic revision --autogenerate -m "add_patient_table"

# Check current migration state
uv run alembic current

# Rollback one step
uv run alembic downgrade -1
```

> **Note:** `DATABASE_URL` must be set in `.env` or environment before running Alembic.

---

## Step Status

| Step | Status | Description |
|------|--------|-------------|
| Step 1 | ✅ Complete | Backend foundation (this implementation) |
| Step 2 | ⬜ Pending | Domain models + persistence layer |
| Step 3 | ⬜ Pending | Document ingestion pipeline |
| Step 4 | ⬜ Pending | Reviewer workflow |
| Step 5 | ⬜ Pending | Async task processing (Celery + Redis) |
| Step 6 | ⬜ Pending | Production hardening + Docker |
# CareIntel
