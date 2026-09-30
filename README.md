<p align="center">
  <img
    width="100%"
    src="https://capsule-render.vercel.app/api?type=waving&amp;height=230&amp;color=0:050505,45:260006,100:8B0000&amp;text=CAREINTEL&amp;fontColor=F6E7E7&amp;fontSize=58&amp;fontAlignY=38&amp;desc=Evidence%20in.%20Human%20judgment%20out.&amp;descAlignY=58&amp;animation=fadeIn&amp;section=header"
    alt="CareIntel — abstract crimson and black banner"
  />
</p>

<div align="center">

# CAREINTEL

### A non-diagnostic, evidence-first backend for human-led healthcare review workflows

CareIntel is a Python backend for turning consent-aware case inputs into traceable evidence, structured processing records, retrieval context, policy-checked AI drafts, and reviewer-controlled outcomes. It is designed as a layered modular monolith with explicit state machines, provider ports, transactional outboxes, and PostgreSQL as the system of record.

<br />

<img src="https://img.shields.io/badge/Python-3.12-111111?style=for-the-badge&amp;logo=python&amp;logoColor=FF4D4D" alt="Python 3.12" />
<img src="https://img.shields.io/badge/FastAPI-0.115%2B-111111?style=for-the-badge&amp;logo=fastapi&amp;logoColor=FF4D4D" alt="FastAPI 0.115 or newer" />
<img src="https://img.shields.io/badge/PostgreSQL-pgvector-111111?style=for-the-badge&amp;logo=postgresql&amp;logoColor=FF4D4D" alt="PostgreSQL with pgvector" />
<img src="https://img.shields.io/badge/version-0.1.0-6E0000?style=for-the-badge" alt="Version 0.1.0" />
<img src="https://img.shields.io/badge/status-engineering%20prototype-6E0000?style=for-the-badge" alt="Engineering prototype" />

<br />
<br />

`◉ EVIDENCE`　`◎ CONTEXT`　`◉ POLICY`　`◎ HUMAN REVIEW`　`◉ AUDIT`

<br />

[Why CareIntel](#what-is-careintel) · [Architecture](#architecture) · [Safety](#ai-safety--human-control) · [API](#api-quick-look) · [Run locally](#run-locally) · [Repository map](#repository-map)

</div>

> [!IMPORTANT]
> CareIntel is explicitly **non-diagnostic**. AI output is modeled as a draft, not a clinical decision. The code keeps approval, rejection, escalation, referral, and completion inside human-controlled workflow states.

---

## What is CareIntel?

Healthcare information arrives as fragments: typed notes, documents, images, recordings, conflicting dates, missing fields, and supporting guidance. CareIntel provides a backend architecture for organizing those fragments into a reviewable case record without assigning decision authority to an AI model.

The repository is aimed at engineers exploring or building reviewer-led healthcare information systems. Its distinctive choices are not a single model or provider, but the boundaries around them:

- domain state machines define legal case, evidence, review, handoff, and task transitions;
- application services coordinate permissions, persistence, audit records, and provider calls;
- infrastructure adapters isolate storage, OCR, speech, embeddings, and LLM integrations;
- PostgreSQL records workflow state, provenance, retrieval runs, AI drafts, policy decisions, and outbox events;
- humans remain responsible for authoritative review outcomes.

### System profile

| Dimension | Current repository |
|---|---|
| Product boundary | Non-diagnostic healthcare information and reviewer workflow backend |
| Runtime | Python 3.12, FastAPI, Uvicorn |
| Architecture | Layered modular monolith with domain, application, infrastructure, persistence, API, and worker packages |
| Source of truth | PostgreSQL through async SQLAlchemy and Alembic |
| Retrieval | PostgreSQL full-text search + pgvector cosine search + reciprocal-rank fusion |
| External providers | Azure Blob Storage, Azure OpenAI, and Azure Document Intelligence adapters |
| Local/test providers | In-memory storage and deterministic demo adapters |
| Async control plane | Database outboxes, durable task records, Celery, and Redis broker configuration |
| Maturity | Active engineering prototype; core flows are substantive, while some later-phase HTTP handlers and worker bodies remain scaffolds |

---

## Capability matrix

| Capability | Implementation | Status |
|---|---|:---:|
| Identity and sessions | Password login, bcrypt hashing, signed JWTs, persisted token sessions, logout revocation | **Implemented** |
| Consent and cases | Consent lifecycle, required active data-processing consent on case creation, case history, optimistic version checks | **Implemented** |
| Evidence intake | Direct text plus configured file allowlist; streamed hashing, size enforcement, magic-byte detection, duplicate detection | **Implemented** |
| Evidence storage | Azure Blob adapter with private-container/SAS behavior; in-memory fallback for local development and tests | **Implemented** |
| OCR and speech | Document OCR and audio transcription service pipelines with Azure and demo provider ports | **Service layer** |
| Text-to-speech | Authenticated binary audio endpoint with Azure OpenAI and demo providers | **API-backed** |
| Language and extraction | Processing services and persistence models; only deterministic demo providers are wired | **Partial** |
| Structuring | Temporal normalization, conflict detection, missing-information evaluation, question generation, and persisted records | **Partial API** |
| Retrieval | Dense pgvector and sparse PostgreSQL FTS search, RRF fusion, reranker port, run/candidate audit records | **Internal service** |
| AI assistance | Azure OpenAI structured-output adapter, demo LLM, draft persistence, provenance policy, approval/rejection service methods | **Internal service** |
| Review and handoff | State machines, ORM models, repositories, and application services exist; incomplete HTTP handlers return explicit `501 NOT_IMPLEMENTED` responses | **Scaffolded API** |
| Async execution | Outbox dispatcher, Celery routing, durable task states, retries, heartbeats, and stale-task recovery | **Partial** |
| Audit and tracing | Application append-only audit repository, ULID correlation IDs, response propagation, structured JSON logging, and sensitive-field redaction; database-level mutation prevention is not enforced | **Partial** |

> **What “partial” means here:** the design and service code exist, but the public or background execution path is not fully wired end to end. The current processing, retrieval, AI, and workflow Celery task bodies persist an explicit failed task state rather than reporting synthetic success, and incomplete structuring/review/handoff routes fail explicitly with `501`.

---

## Technology system

<div align="center">

<img src="https://skillicons.dev/icons?i=python,fastapi,postgres,redis,azure&amp;theme=dark" alt="Python, FastAPI, PostgreSQL, Redis, and Azure" />

</div>

| Plane | Technology | Repository role |
|---|---|---|
| **Core** | Python 3.12 · FastAPI · Pydantic Settings · Uvicorn | ASGI API, schemas, dependency injection, typed environment configuration |
| **Data** | PostgreSQL · asyncpg · SQLAlchemy 2 · Alembic | Transactional persistence, repositories, migrations, JSONB records |
| **Search** | pgvector · PostgreSQL `tsvector`/GIN · HNSW | Dense and sparse retrieval over versioned knowledge chunks |
| **Async** | Celery · Redis | Brokered task dispatch, retry policy, queue routing, task lifecycle tracking |
| **Storage** | Azure Blob Storage · in-memory fake adapter | Evidence objects and short-lived download URLs |
| **AI / ML** | Azure OpenAI · OpenAI SDK · tiktoken | Structured LLM output, 1,536-dimension embeddings, STT, and TTS adapters |
| **Document AI** | Azure AI Document Intelligence | Layout/read OCR adapter |
| **Security** | PyJWT · bcrypt · FastAPI HTTP Bearer | JWT verification, persisted revocation, password hashing, permission dependencies |
| **Quality** | pytest · pytest-asyncio · HTTPX · Ruff · mypy | Unit/API/integration testing, formatting, linting, and strict typing configuration |
| **Packaging** | uv · Hatchling | Locked dependency workflow and package builds |

Provider selection is configuration-driven. Development and test environments may use demo or in-memory implementations. Production configuration fails closed unless the wired LLM, embedding, OCR, STT, and TTS capabilities select fully configured external adapters.

---

## Architecture

CareIntel keeps domain rules independent of FastAPI and SQLAlchemy. The API resolves request-scoped dependencies, application services execute use cases, repositories persist state, and infrastructure adapters sit behind narrow protocols.

```mermaid
flowchart TB
    client[Client / reviewer UI]

    subgraph edge[API edge]
        api[FastAPI /api/v1]
        middleware[Correlation ID · CORS · error contract]
        auth[JWT session validation · permission dependencies]
    end

    subgraph app[Application layer]
        cases[Case · consent · evidence services]
        processing[OCR · STT · language · extraction services]
        intelligence[Structuring · retrieval · AI services]
        review[Review · escalation · handoff services]
        asyncctl[Outbox dispatcher · durable task service]
    end

    subgraph domain[Pure domain]
        states[State machines]
        policies[Authorization · consent · AI provenance policy]
        contracts[Commands · value objects · provider protocols]
    end

    subgraph data[Persistence]
        repos[SQLAlchemy repositories]
        postgres[(PostgreSQL)]
        search[(FTS + pgvector)]
        audit[(Audit logs · histories · outboxes)]
    end

    subgraph providers[Infrastructure adapters]
        blob[Azure Blob / in-memory storage]
        multimodal[Azure OCR · STT · TTS / demo adapters]
        llm[Azure OpenAI / demo LLM + embeddings]
        broker[Celery + Redis]
    end

    client --> api --> middleware --> auth
    auth --> cases
    auth --> processing
    cases --> states
    processing --> contracts
    intelligence --> policies
    review --> states
    cases --> repos
    processing --> repos
    intelligence --> repos
    review --> repos
    repos --> postgres
    postgres --- search
    repos --> audit
    cases --> blob
    processing --> multimodal
    intelligence --> llm
    cases --> asyncctl
    processing --> asyncctl
    asyncctl --> broker

    classDef crimson fill:#3b0508,stroke:#ff4d5a,color:#fff;
    classDef dark fill:#101014,stroke:#8d3038,color:#eee;
    classDef data fill:#1a1014,stroke:#c63b48,color:#fff;
    class api,auth,cases,intelligence,review crimson;
    class middleware,processing,asyncctl,states,policies,contracts dark;
    class repos,postgres,search,audit,blob,multimodal,llm,broker data;
```

### Architectural boundaries

```text
HTTP / ASGI
    │
    ▼
api/               request parsing, auth dependencies, response contracts
    │
    ▼
application/       use-case orchestration and transaction-aware services
    │
    ├──────────► domain/          framework-free states, commands, policies
    │
    ├──────────► persistence/     ORM models and repository implementations
    │
    └──────────► infrastructure/  provider ports and Azure/demo adapters
                          │
                          ▼
workers/           Celery entry points and durable task lifecycle handling
```

The architecture test suite enforces important import boundaries, including a framework-independent domain layer.

---

## Evidence and intelligence flow

Solid arrows below represent currently API-backed transitions. Dashed arrows represent implemented service-layer capabilities whose full public/worker orchestration is still incomplete.

```mermaid
flowchart LR
    consent[Active consent] --> case[Case]
    case --> input{Evidence input}
    input -->|text| text[(PostgreSQL text record)]
    input -->|file| validate[Stream · validate · SHA-256]
    validate --> object[(Blob storage)]
    validate --> meta[(Evidence metadata)]
    text --> ready[READY]
    meta --> scan[Content scanner port]
    scan -->|clean| ready
    scan -->|default no-op| stored[STORED]

    ready -. service invocation .-> process[OCR / STT / language / extraction]
    process -.-> structured[Candidates · timeline · conflicts · missing info]
    structured -.-> retrieve[Hybrid knowledge retrieval]
    retrieve -.-> draft[Structured AI draft]
    draft -.-> policy{Provenance policy}
    policy -. fail .-> blocked[POLICY_BLOCKED / rejected]
    policy -. pass .-> human[Human reviewer]
    human -.-> outcome[Decision · escalation · referral / handoff]

    case --> audit[(History · audit · correlation)]
    validate --> audit
    process -.-> audit
    retrieve -.-> audit
    policy -.-> audit
    human -.-> audit

    classDef crimson fill:#45070b,stroke:#ff4d5a,color:#fff;
    classDef dark fill:#111116,stroke:#8d3038,color:#eee;
    classDef warn fill:#2c2020,stroke:#d49b54,color:#fff;
    class consent,case,ready,draft,human crimson;
    class input,validate,process,structured,retrieve,policy,outcome dark;
    class stored,blocked warn;
```

The default `NoOpScanner` returns `PENDING`, so uploaded files remain `STORED` unless a real scanner returns `CLEAN`. Direct text evidence is created as `READY`.

---

## Durable async workflow

The asynchronous control plane uses PostgreSQL for durable workflow state and Redis/Celery for delivery. The task model is idempotency-keyed, and workers use late acknowledgement, retry backoff, low prefetch, time limits, and a stale-task sweep.

```mermaid
sequenceDiagram
    autonumber
    participant API as FastAPI service
    participant DB as PostgreSQL
    participant D as Outbox dispatcher
    participant R as Redis broker
    participant W as Celery worker

    API->>DB: Write domain change + outbox/task record
    DB-->>API: Commit authoritative state
    loop Poll unpublished events
        D->>DB: SELECT ... FOR UPDATE SKIP LOCKED
        D->>DB: Get/create task by idempotency key
        D->>R: Send routed Celery task
        D->>DB: Mark event published and task QUEUED
    end
    R-->>W: Deliver task
    W->>DB: QUEUED → RUNNING
    Note over W: Current processing/retrieval/AI bodies simulate execution
    W->>DB: RUNNING → SUCCEEDED or FAILED
    D->>R: Schedule stale-task recovery sweep
```

This is an **at-least-once-oriented design**, not an exactly-once claim. Database uniqueness constraints, explicit state machines, and idempotency keys provide the duplicate-work controls represented in the code.

---

## Data model

Alembic migrations define the current PostgreSQL schema, including the `vector` extension, generated full-text vectors, GIN indexes, and an HNSW cosine index.

| Area | Principal records |
|---|---|
| Identity | users, roles, permissions, user-role grants, role-permission grants, token sessions |
| Consent and audit | consents, consent events, audit logs |
| Cases | cases, encounters, case state history, case outbox |
| Evidence | evidence, text content, evidence state history, evidence outbox |
| Processing | processing runs, OCR pages/regions/tables, transcript runs/segments, language results, extraction runs/candidates |
| Structuring | structuring runs, timeline events, conflict records, checklist versions, missing-info items, clarification questions |
| Knowledge and retrieval | sources, immutable versions, chunks, embedding versions, chunk embeddings, retrieval runs/candidates |
| AI control | AI runs, AI drafts, claim provenance payloads, deterministic policy decisions |
| Review and handoff | queue items, decisions, notes, draft edit versions, escalations, recipients, referral packages, handoffs |
| Async workflow | durable async tasks with idempotency, causation, heartbeat, attempts, result, and failure metadata |

---

## AI safety & human control

```mermaid
flowchart LR
    trusted[Application-controlled instructions]
    untrusted[Evidence and retrieved passages]
    context[SafeContext]
    model[LLM provider]
    parse[Structured JSON result]
    draft[AIDraft: DRAFT]
    provenance[Deterministic provenance check]
    reject[Rejected / policy blocked]
    reviewer[Qualified human reviewer]
    approved[Approved draft]

    trusted --> context
    untrusted --> context
    context -->|separate system/user messages| model
    model --> parse --> draft --> provenance
    provenance -->|invalid source IDs| reject
    provenance -->|pass| reviewer
    reviewer -->|reject or edit| reject
    reviewer -->|explicit approval| approved

    classDef crimson fill:#45070b,stroke:#ff4d5a,color:#fff;
    classDef dark fill:#111116,stroke:#8d3038,color:#eee;
    classDef blocked fill:#29191b,stroke:#d49b54,color:#fff;
    class context,draft,reviewer crimson;
    class trusted,untrusted,model,parse,provenance,approved dark;
    class reject blocked;
```

The current safeguards are concrete and deliberately bounded:

- external passages are separated from application-controlled system instructions and labeled by origin;
- the Azure adapter requests strict JSON-schema structured output;
- unparseable model output is rejected by the service;
- AI runs, hashes, token usage, drafts, and policy outcomes are persisted;
- the default deterministic policy checks that cited source IDs exist in the supplied context;
- failed policy evaluation rejects the draft; a model cannot approve itself;
- domain contracts prohibit diagnostic conclusions, prescriptions, and autonomous clinical decisions.

These controls are not a claim of comprehensive model safety or prompt-injection immunity. The default policy suite currently contains one provenance-integrity rule, and the AI/review path is not exposed as a complete public API workflow.

---

## Security model

| Control | Current mechanism |
|---|---|
| Authentication | HTTP Bearer JWT with required subject, session, JTI, issuer, audience, issued-at, and expiry claims |
| Session invalidation | Database-backed token sessions; missing or revoked JTIs are rejected |
| Password storage | bcrypt with cost factor 12 |
| Authorization | Deny-by-default permission evaluator plus FastAPI permission dependencies |
| Consent | Active subject/purpose/notice-version check before case creation |
| Object access | Case/evidence services re-check permissions and mask unauthorized case lookup as not found |
| Concurrency | Expected aggregate version on case transitions |
| Upload controls | Extension allowlist, basename sanitization, maximum size, magic-byte detection, SHA-256 deduplication |
| Secret handling | Pydantic `SecretStr`, environment-driven configuration, masked database URLs |
| Logs and errors | JSON logging, sensitive-field redaction, no request-body logging, normalized error envelope |
| Traceability | `X-Correlation-ID` propagation plus audit and state-history records |
| Production guards | Debug/SQL echo rejection, required Redis/Azure storage, and fail-closed external provider configuration in production mode |

Two boundaries matter today: comprehensive cross-object authorization coverage has not been demonstrated for every later-phase resource, and the default scanner is a no-op that never declares file content clean. Facility-role mappings are loaded into the request context and a missing mapping no longer grants facility access.

No compliance certification is claimed by this repository.

---

## API quick look

All routes are versioned below `/api/v1`. Interactive documentation is generated by FastAPI at [`/api/docs`](http://127.0.0.1:8000/api/docs), with ReDoc at [`/api/redoc`](http://127.0.0.1:8000/api/redoc) and the schema at [`/api/openapi.json`](http://127.0.0.1:8000/api/openapi.json).

| Area | Representative routes | Behavior |
|---|---|---|
| Health | `GET /health/live` · `GET /health/ready` | Process liveness and database, Redis, and storage-aware readiness |
| Authentication | `POST /auth/login` · `POST /auth/logout` · `GET /auth/me` | Access-token issuance, revocation, and current profile |
| Consent | `POST /consent/request` · `POST /consent/{id}/capture` · `DELETE /consent/{id}` | Request, activate, and withdraw consent |
| Cases | `POST /cases` · `GET /cases/{id}` · `POST /cases/{id}/transitions` · `GET /cases/{id}/history` | Create, read, transition, and audit case state |
| Evidence | `POST /evidence/text` · `POST /evidence/files` · `GET /evidence/{id}` · `GET /evidence/{id}/download` | Register text, stream uploads, inspect metadata, request a download URL |
| Processing | `POST /processing/trigger` | Create an outbox-backed durable processing task |
| Tasks | `GET /tasks/{id}` · `GET /cases/{id}/tasks` | Inspect task state and list case tasks |
| Audio | `POST /audio/speech` | Return synthesized audio from the configured TTS provider |

The generated OpenAPI document also exposes structuring, review, escalation, and handoff routes. They are intentionally omitted from the table above because incomplete handlers return `501 NOT_IMPLEMENTED` rather than complete persisted workflows.

### Error contract

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource was not found.",
    "correlation_id": "01J..."
  }
}
```

Every response carries an `X-Correlation-ID`; callers may supply one and receive it back.

---

## Run locally

### Prerequisites

- Python `3.12.x`
- [`uv`](https://docs.astral.sh/uv/)
- PostgreSQL with the `pgvector` extension available
- Redis only when exercising Celery-backed flows
- Azure credentials only when selecting Azure providers

### 1. Install

```bash
git clone https://github.com/Adi-7i/CareIntel.git
cd CareIntel
uv sync --all-extras
```

### 2. Configure

```bash
cp .env.example .env
```

At minimum, set all three required secrets/DSNs shown below. `.env.example` contains every JWT field and provider deployment/version field without real values.

```dotenv
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME
SECRET_KEY=replace-with-a-long-random-value
JWT_SECRET_KEY=replace-with-a-different-long-random-value
```

For a local run without Azure calls, select the repository's deterministic/demo providers:

```dotenv
LLM_PROVIDER=demo
EMBEDDING_PROVIDER=demo
OCR_PROVIDER=demo
STT_PROVIDER=demo
TTS_PROVIDER=demo
LANGUAGE_DETECTION_PROVIDER=demo
TRANSLATION_PROVIDER=demo
EXTRACTION_PROVIDER=demo
AZURE_OPENAI_API_KEY=
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=
AZURE_STORAGE_CONNECTION_STRING=
CORS_ALLOWED_ORIGINS=["http://localhost:3000"]
```

> [!NOTE]
> Without `AZURE_STORAGE_CONNECTION_STRING`, evidence objects use an in-memory store and disappear when the process restarts. The demo embedding provider produces deterministic test vectors, not semantic embeddings.

### 3. Migrate and start

```bash
uv run alembic upgrade head
uv run uvicorn careintel.main:app --reload --host 127.0.0.1 --port 8000
```

Then open <http://127.0.0.1:8000/api/docs>.

### 4. Optional async infrastructure

Set `REDIS_URL`, then start a worker for the queues represented in the dispatcher:

```bash
uv run celery -A careintel.workers.celery_app:celery_app worker \
  --loglevel=INFO \
  -Q careintel_default,careintel_processing,careintel_retrieval,careintel_ai,careintel_workflow
```

A continuously running `UnifiedOutboxDispatcher` must also be hosted by an application process; the repository currently provides the dispatcher class but no dedicated CLI entry point for it.

---

## Configuration map

| Concern | Key settings | Default/fallback behavior |
|---|---|---|
| Application | `APP_ENV`, `APP_DEBUG`, `APP_HOST`, `APP_PORT`, `APP_LOG_LEVEL` | Development mode, loopback host, port 8000 |
| Database | `DATABASE_URL`, pool size/overflow/timeout | Required asyncpg DSN |
| JWT | `JWT_SECRET_KEY`, algorithm, TTL, issuer, audience | HS256, 30-minute access token |
| Evidence | max size, extensions, SAS TTL, scan requirement | 50 MiB, explicit allowlist, 15-minute URL |
| Blob storage | Azure connection string and container | In-memory fake when connection string is absent |
| LLM/embeddings | provider, endpoint, key, deployment | Demo providers unless Azure is selected and keyed |
| OCR | provider, Document Intelligence endpoint/key/model | Demo OCR fallback |
| STT/TTS | provider and Azure deployment/API-version settings | Demo speech providers |
| Async | `REDIS_URL`, Celery queue/prefetch/time limits | Local Redis broker URL fallback for Celery |

Configured upload extensions are `.pdf`, `.docx`, `.txt`, `.jpg`, `.jpeg`, `.png`, `.mp3`, `.wav`, `.m4a`, and `.ogg`.

---

## Repository map

```text
CareIntel/
├── src/careintel/
│   ├── main.py                 # Composition root and application lifespan
│   ├── api/
│   │   ├── deps.py             # Request-scoped dependency wiring
│   │   └── v1/                 # Versioned FastAPI routers and schemas
│   ├── application/            # Use cases and workflow orchestration
│   │   ├── ai/                 # AI execution and deterministic policy checks
│   │   ├── auth/               # Login, JWT, permissions, consent
│   │   ├── case/               # Case lifecycle service
│   │   ├── evidence/           # Intake, validation, storage coordination
│   │   ├── processing/         # OCR, STT, language, extraction pipelines
│   │   ├── retrieval/          # Dense/sparse search and fusion
│   │   ├── review/             # Review workspace and draft decisions
│   │   └── workflow/           # Durable tasks and outbox dispatch
│   ├── domain/                 # Framework-free models, enums, policies, states
│   ├── infrastructure/         # Azure, demo, fake, no-op, and provider ports
│   ├── persistence/
│   │   ├── models/             # SQLAlchemy ORM model families
│   │   └── repositories/       # Persistence operations by aggregate
│   └── workers/                # Celery app, task entry points, worker context
├── migrations/                 # Alembic revisions 0001–0010
├── scripts/                    # Admin seed and provider/infra verification tools
├── tests/
│   ├── unit/                   # Domain and service tests
│   ├── api/                    # ASGI-level endpoint tests
│   ├── integration/            # Live PostgreSQL checks
│   └── e2e/                    # Synthetic golden-path coverage
├── .env.example                # Configuration template
├── pyproject.toml              # Dependencies and tool configuration
└── uv.lock                     # Reproducible dependency lock
```

---

## Engineering principles encoded in the code

| Principle | Concrete expression |
|---|---|
| **Human authority** | AI outputs are drafts; domain states reserve review and disposition for people |
| **Evidence before generation** | Safe context carries source origin, locator, and IDs; provenance is checked after generation |
| **Explicit uncertainty** | Conflicts, missing information, clarification questions, and policy outcomes are first-class records |
| **Deterministic transitions** | State machines reject illegal case, evidence, review, handoff, and task transitions |
| **Traceable mutation** | Case/evidence changes create histories, audit entries, and outbox records |
| **Provider isolation** | Protocols separate application logic from Azure, demo, in-memory, and no-op implementations |
| **Transactional durability** | PostgreSQL holds authoritative domain, task, audit, and outbox state |
| **Idempotent intent** | Checksums, unique constraints, input hashes, versions, and task idempotency keys suppress duplicate work |
| **Conservative failure** | Missing auth, revoked sessions, invalid consent, illegal transitions, and invalid provenance fail closed |

---

## Validation and development commands

```bash
# Tests that do not require live infrastructure
uv run pytest

# Live-database integration tests
uv run pytest tests/integration/ -m integration -v

# Formatting, linting, and strict type checking
uv run ruff format --check src/careintel tests scripts
uv run ruff check src/careintel tests scripts
uv run mypy src/careintel
```

The repository has unit, API, infrastructure, integration, and synthetic end-to-end test modules. No CI workflow is tracked in the current tree, so this README intentionally shows no build, coverage, or deployment-status badge.

---

## Current implementation boundary

CareIntel is best read as a substantial architecture prototype, not a production deployment claim.

- **API-backed now:** health, authentication, consent, case management, evidence intake/download, TTS, processing-task submission, and task inspection.
- **Implemented internally:** multimodal processing services, structuring logic, hybrid retrieval, AI draft/policy services, review/handoff domain and persistence layers.
- **Not end-to-end yet:** real content scanning, complete worker-to-service execution, public knowledge/retrieval/AI APIs, and persisted behavior behind several review/escalation/handoff routes.
- **Environment-specific release evidence:** [`RELEASE_EVIDENCE.md`](RELEASE_EVIDENCE.md) records the external checks actually executed on the configured environment; it must not be generalized to another deployment.

There is currently no repository license file, release workflow, or deployment manifest. Docker is deliberately excluded from this release scope.

---

<div align="center">

### ◉ Controlled complexity. Traceable evidence. Human judgment.

Built as a backend architecture study for auditable, reviewer-led healthcare information workflows.

[OpenAPI](http://127.0.0.1:8000/api/docs) · [Issues](https://github.com/Adi-7i/CareIntel/issues) · [Back to top](#careintel)

</div>

<p align="center">
  <img
    width="100%"
    src="https://capsule-render.vercel.app/api?type=waving&amp;height=120&amp;color=0:8B0000,55:260006,100:050505&amp;section=footer"
    alt="Crimson and black footer wave"
  />
</p>
