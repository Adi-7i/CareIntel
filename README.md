# CareIntel Backend Infrastructure

> **Enterprise-Grade Healthcare Information & Reviewer-Workflow System**
>
> *A non-diagnostic platform designed to empower qualified human review while strictly utilizing synthetic or public sample data.*

---

## 📑 Table of Contents
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Execution Methods & Runbooks](#execution-methods--runbooks)
  - [Prerequisites](#prerequisites)
  - [Environment Provisioning](#environment-provisioning)
  - [Database Operations](#database-operations)
  - [Service Execution](#service-execution)
- [Code Quality & Testing Verification](#code-quality--testing-verification)
- [Architecture Principles](#architecture-principles)
- [Roadmap & Milestone Tracking](#roadmap--milestone-tracking)

---

## 🏛️ System Architecture

CareIntel relies on a deeply layered architecture enforcing strict separation of concerns, decoupling the domain logic from the underlying framework operations.

```mermaid
graph TD
    %% Define styles
    classDef client fill:#3498db,stroke:#2980b9,stroke-width:2px,color:white;
    classDef api fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:white;
    classDef domain fill:#f1c40f,stroke:#f39c12,stroke-width:2px,color:black;
    classDef db fill:#9b59b6,stroke:#8e44ad,stroke-width:2px,color:white;
    classDef external fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:white;

    %% Nodes
    Client((Client App)):::client
    Router[FastAPI Router / API Layer]:::api
    Deps[Dependency Injection / Auth]:::api
    Domain[Pure Domain Layer]:::domain
    Core[Core Infrastructure / Config]:::domain
    PostgreSQL[(PostgreSQL DB)]:::db
    Celery[Celery / Task Queue]:::external
    Redis[(Redis Streams)]:::db

    %% Connections
    Client -->|HTTPS / REST| Router
    Router --> Deps
    Deps -->|Validates| Core
    Router -->|Calls| Domain
    Domain -->|CRUD via SQLAlchemy| PostgreSQL
    Domain -->|Async Jobs| Celery
    Celery -->|State/Msg| Redis

    %% Subgraphs
    subgraph CareIntel Backend System
        Router
        Deps
        Domain
        Core
    end
```

---

## 💻 Technology Stack

CareIntel leverages modern, high-performance tooling to guarantee reliability, type safety, and scalability.

| Domain | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.12+ | Strongly typed, modern Python standards |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) | Extremely fast Python package installer and resolver |
| **Framework** | FastAPI | High-performance async web framework |
| **Database** | PostgreSQL | Enterprise-grade relational database |
| **ORM & Migrations** | SQLAlchemy 2.0 & Alembic | Async persistence and schema versioning |
| **Task Queue** | Celery & Redis (Planned) | Distributed task orchestration |
| **Linting & Formatting** | Ruff & Mypy | Strict static analysis and unified linting |
| **Storage** | Azure Blob Storage | Secure, scalable evidence storage |

---

## ⚙️ Execution Methods & Runbooks

Follow these procedures to bootstrap the environment and start the development server.

### Prerequisites

Ensure the following dependencies are installed on your host system:
- **Python 3.12**
- **uv** package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **PostgreSQL** instance (local or remote)

### Environment Provisioning

1. **Synchronize Dependencies:**
   Install the project with all required development and production packages.
   ```bash
   uv sync --all-extras
   ```

2. **Configure Environment Parameters:**
   Establish your local `.env` file from the provided template.
   ```bash
   cp .env.example .env
   ```
   **Crucial Environment Variables:**
   - `DATABASE_URL`: Standard async Postgres connection string (e.g., `postgresql+asyncpg://user:pass@host:port/dbname`)
   - `SECRET_KEY`: High-entropy key for cryptographic signing (`openssl rand -hex 32`)

### Database Operations

Schema synchronization and migrations are managed by Alembic. The database connection is dynamically resolved via the `DATABASE_URL` environment parameter.

```bash
# Apply pending migrations to establish schema
uv run alembic upgrade head

# Generate a new migration blueprint
uv run alembic revision --autogenerate -m "descriptive_migration_name"

# Verify current revision state
uv run alembic current

# Revert the most recent migration step
uv run alembic downgrade -1
```

### Service Execution

Launch the API server bound to the local interface.

```bash
uv run uvicorn careintel.main:app --reload --host 127.0.0.1 --port 8000
```
> **Telemetry & Documentation:**
> - API Documentation: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
> - Liveness Probe: `GET /api/v1/health/live`
> - Readiness Probe: `GET /api/v1/health/ready`

---

## 🧪 Code Quality & Testing Verification

CareIntel maintains rigorous code quality standards. Ensure all checks succeed prior to committing changes. Commands should be executed from the project root.

### Code Style & Type Safety
```bash
# Format codebase in-place
uv run ruff format .

# Execute static linting checks
uv run ruff check .

# Perform strict type analysis
uv run mypy
```

### Automated Testing

The testing suite partitions unit, API, and integration constraints to optimize developer velocity.

```bash
# Execute isolated unit and API tests (No live DB required)
uv run pytest

# Generate test coverage reports
uv run pytest --cov

# Execute full integration suite (Requires live DATABASE_URL)
uv run pytest tests/integration/ -m integration -v
```

---

## 📐 Architecture Principles

Our technical decisions prioritize maintainability, security, and traceability:

1. **Dependency Inversion & Layer Isolation:**
   - **Domain Layer:** Contains raw business logic. Strictly prohibits `FastAPI`, `SQLAlchemy`, or any volatile external framework imports.
   - **Core Layer:** Manages foundational elements (Pydantic, stdlib).
   - **API Layer:** Interfaces with HTTP requests but never bypasses the domain to interact directly with persistence engines.
2. **Deterministic Error Handling:**
   All public API faults adhere to a strict JSON contract to ensure predictable client consumption:
   ```json
   {
     "error": {
       "code": "NOT_FOUND",
       "message": "The requested resource was not found.",
       "correlation_id": "01H..."
     }
   }
   ```
3. **Traceability:**
   Every request is tagged with a time-sortable ULID (`X-Correlation-ID`) acting as a universal context tracer across services and logs.
4. **Security by Design:**
   - Imperative reliance on environment variables for sensitive parameters.
   - Automatic redaction of sensitive telemetry (e.g., tokens, passwords).
   - Opaque error stack traces in production environments.

---

## 🗺️ Roadmap & Milestone Tracking

| Phase | Milestone | Execution Status |
| :---: | :--- | :--- |
| **1** | Backend Infrastructure & Architectural Foundation | ✅ **Complete** |
| **2** | Domain Modeling & Persistence Implementations | ⬜ Pending |
| **3** | Document Ingestion Pipelines | ⬜ Pending |
| **4** | Human-in-the-Loop Reviewer Workflow | ⬜ Pending |
| **5** | Asynchronous Task Orchestration (Celery + Redis) | ⬜ Pending |
| **6** | Production Hardening & Docker Containerization | ⬜ Pending |

---
*Maintained with engineering rigor by the CareIntel Systems Architecture Team.*
