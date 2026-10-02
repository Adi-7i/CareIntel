# CareIntel Backend Startup and Operations Guide

This is the canonical startup and operational onboarding guide for the current CareIntel backend.
Run commands from the repository root unless a section explicitly says otherwise. The commands
below reflect the current `pyproject.toml`, application composition root, migrations, scripts,
workers, and API routes.

CareIntel is a non-diagnostic, human-in-the-loop healthcare triage-support backend. PostgreSQL is
the authoritative store for application and workflow state. Redis and Celery deliver asynchronous
work but do not own business state. Azure Blob Storage holds source evidence objects. Azure AI
adapters provide bounded OCR, speech, embedding, and advisory-generation capabilities; they do not
approve cases or control workflow transitions.

## Current architecture

| Concern | Current implementation |
|---|---|
| API | Python 3.12, FastAPI, Pydantic, Uvicorn |
| Application design | Layered modular monolith: API, application, domain, persistence, infrastructure, workers |
| Authoritative state | PostgreSQL through async SQLAlchemy and Alembic |
| Retrieval | PostgreSQL full-text search plus pgvector, with deterministic fusion |
| Binary evidence | Private Azure Blob Storage in production; process-local in-memory storage in development when unconfigured |
| Async delivery | PostgreSQL transactional outboxes, durable task rows, Redis, Celery, and a separate outbox dispatcher process |
| Authentication | Email/password login, bcrypt password hashes, JWT access tokens, persisted token sessions |
| Authorization | Database-backed roles and permissions plus facility scope checks |
| Safety | Consent checks, deterministic validation/policy services, human review, append-only database audit records |
| External AI | Azure OpenAI-compatible LLM, embeddings, STT/diarization, TTS, and Azure Document Intelligence OCR |

The ASGI entry point is `careintel.main:app`. API routes are under `/api/v1`.

## 1. Prerequisites

The documented shell commands assume a POSIX environment such as Linux or macOS. Native Windows
commands have not been validated and are **REQUIRES MANUAL CONFIGURATION**.

- **Git** is required to clone and update the repository.
- **Python 3.12.x** is required. `.python-version` specifies `3.12`, and `pyproject.toml` accepts
  Python `>=3.12,<3.13`.
- **uv** is the canonical dependency and virtual-environment tool because the repository commits
  `uv.lock`. A pip-only installation is **REQUIRES MANUAL CONFIGURATION** and does not reproduce
  the lock file by itself.
- **libmagic** must be available to the operating system. The `python-magic` package uses it for
  upload MIME detection. Installation is operating-system-specific.
- **An external PostgreSQL database**, such as Supabase PostgreSQL, is required. The application
  does not ship or install PostgreSQL.
- **pgvector** must be available to PostgreSQL. Migration `0007` executes
  `CREATE EXTENSION IF NOT EXISTS vector`.
- **An external Redis service** is required for production and for Celery-backed development.
  The repository does not install Redis.
- **Azure resources** are required for production: private Blob Storage, an Azure OpenAI-compatible
  resource with the configured deployments, and Azure Document Intelligence.
- **curl** is optional but used in the API examples below.

Azure CLI, PostgreSQL CLI, Docker, Gunicorn, and a process supervisor are not repository
requirements. Docker is not part of this project. Production TLS termination, reverse proxying,
service supervision, secret injection, and log shipping are **REQUIRES MANUAL CONFIGURATION**.

## 2. Clone and install

```bash
git clone https://github.com/Adi-7i/CareIntel.git
cd CareIntel
uv sync --all-extras --frozen
source .venv/bin/activate
```

`uv sync` creates `.venv` when needed, installs the package in editable form, installs runtime and
development dependencies, and uses the committed lock without updating it. To check an existing
environment without changing it:

```bash
uv sync --all-extras --frozen --check
```

Important repository paths:

```text
src/careintel/             application package
migrations/                Alembic environment and ordered schema revisions
scripts/                   operational and verification commands
config/checklists/         versioned structuring checklist configuration
tests/                     unit, API, infrastructure, integration, and E2E tests
.env.example               non-secret configuration template
```

## 3. Environment configuration

`careintel.core.config.Settings` uses `pydantic-settings` and reads variables from the process
environment and then `.env`. Process environment variables take precedence over `.env`. `.env` is
resolved relative to the working directory, so run commands from the repository root. Settings are
cached per process after their first load.

Create a local configuration file:

```bash
cp .env.example .env
chmod 600 .env
```

`.env`, `.env.local`, `.env.production`, and `.env.*.local` are ignored by Git. Never commit real
secrets. In a deployed environment, prefer the platform's secret manager or environment injection
instead of copying a secret-bearing file into the image or release artifact.

### Required in every environment

```dotenv
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE?ssl=require
SECRET_KEY=YOUR_LONG_RANDOM_APPLICATION_SECRET
JWT_SECRET_KEY=YOUR_DIFFERENT_LONG_RANDOM_JWT_SECRET
```

- `DATABASE_URL` must use `postgresql+asyncpg://`; synchronous `postgresql://` and `postgres://`
  URLs are rejected.
- URL-encode reserved characters in database credentials.
- `SECRET_KEY` and `JWT_SECRET_KEY` must be different, high-entropy secrets.

### Application

| Variable | Default | Notes |
|---|---:|---|
| `APP_ENV` | `development` | `development`, `testing`, `staging`, or `production` |
| `APP_DEBUG` | `false` | Must be false in production |
| `APP_HOST` | `127.0.0.1` | Configuration metadata; pass the bind host explicitly to Uvicorn |
| `APP_PORT` | `8000` | Configuration metadata; pass the port explicitly to Uvicorn |
| `APP_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `CORS_ALLOWED_ORIGINS` | empty | Supply a JSON list, for example `'["https://app.example.com"]'` |

Complex list settings use JSON syntax. If overriding `EVIDENCE_ALLOWED_EXTENSIONS`, use a JSON list
as well.

### Database and dependency timeouts

| Variable | Default |
|---|---:|
| `DATABASE_POOL_SIZE` | `10` |
| `DATABASE_MAX_OVERFLOW` | `5` |
| `DATABASE_POOL_TIMEOUT` | `30` seconds |
| `DEPENDENCY_CONNECT_TIMEOUT_SECONDS` | `10` seconds |
| `READINESS_TIMEOUT_SECONDS` | `30` seconds per probe |
| `DATABASE_ECHO_SQL` | `false` |

`DATABASE_ECHO_SQL=true` is rejected in production.

### JWT

| Variable | Default |
|---|---|
| `JWT_ALGORITHM` | `HS256` |
| `JWT_ACCESS_TOKEN_TTL_MINUTES` | `30` |
| `JWT_ISSUER` | `careintel` |
| `JWT_AUDIENCE` | `careintel-api` |

Changing these values invalidates assumptions made by existing tokens. JWT signing-key rotation is
**NOT CURRENTLY SUPPORTED** as a multi-key/key-ID workflow.

### Evidence and Blob Storage

| Variable | Default or requirement |
|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | Required in production |
| `AZURE_STORAGE_CONTAINER` | `careintel-evidence` |
| `EVIDENCE_MAX_FILE_SIZE_BYTES` | `52428800` (50 MiB) |
| `EVIDENCE_ALLOWED_EXTENSIONS` | PDF, DOCX, TXT, JPG/JPEG, PNG, MP3, WAV, M4A, OGG |
| `EVIDENCE_SAS_TTL_MINUTES` | `15` |
| `EVIDENCE_REQUIRE_SCAN_BEFORE_READY` | `true` |

When no Blob connection is configured outside production, the application uses an in-memory store
whose contents disappear on process restart. Production rejects missing Blob configuration.

The current content scanner is `NoOpScanner`, which returns `PENDING`. A real malware/content
scanner is **NOT CURRENTLY SUPPORTED**. Uploaded files therefore remain `STORED` when scan-before-
ready is enabled; direct text evidence can be `READY`.

### Redis and Celery

| Variable | Default or behavior |
|---|---|
| `REDIS_URL` | Required in production; canonical Celery broker and result backend when present |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0`, development fallback only |
| `CELERY_RESULT_BACKEND` | Optional development fallback when `REDIS_URL` is absent |
| `CELERY_TASK_DEFAULT_QUEUE` | `careintel_default` |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | `1` |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `300` seconds |
| `CELERY_TASK_HARD_TIME_LIMIT` | `360` seconds |
| `CELERY_STALE_TASK_THRESHOLD_SECONDS` | `120` seconds |

### Azure OpenAI-compatible providers

Production requires these provider selectors:

```dotenv
LLM_PROVIDER=azure_openai
EMBEDDING_PROVIDER=azure_openai
STT_PROVIDER=azure_openai_diarize
TTS_PROVIDER=azure_openai
OCR_PROVIDER=azure_document_intelligence
```

`STT_PROVIDER=azure_openai_transcribe` is also accepted when diarization is not required.

Configure the corresponding resource and deployments:

```dotenv
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.openai.azure.com/
AZURE_OPENAI_API_KEY=YOUR_AZURE_OPENAI_KEY
AZURE_LLM_DEPLOYMENT=YOUR_STRUCTURED_OUTPUT_DEPLOYMENT
AZURE_LLM_API_VERSION=2024-08-01-preview
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_STT_DEPLOYMENT=gpt-4o-mini-transcribe
AZURE_STT_DIARIZE_DEPLOYMENT=gpt-4o-transcribe-diarize
AZURE_TTS_DEPLOYMENT=tts-hd
AZURE_STT_API_VERSION=2025-03-01-preview
AZURE_STT_DIARIZE_API_VERSION=2025-03-01-preview
AZURE_TTS_API_VERSION=2025-03-01-preview
AZURE_TTS_VOICE=nova
```

The embedding adapter and database schema expect 1,536-dimensional vectors. The embedding adapter
currently uses Azure API version `2024-02-15-preview` internally; it is not separately configurable.

### Azure Document Intelligence

```dotenv
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://YOUR_RESOURCE.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=YOUR_DOCUMENT_INTELLIGENCE_KEY
AZURE_DI_MODEL=prebuilt-layout
OCR_TEMP_WORKSPACE=/tmp/careintel_ocr
```

The configured process user must be able to create and write `OCR_TEMP_WORKSPACE`.

### Demo-only processing providers

The application and worker composition roots currently wire deterministic demo implementations for
language detection, translation, and structured extraction regardless of selector values:

```dotenv
LANGUAGE_DETECTION_PROVIDER=demo
TRANSLATION_PROVIDER=demo
EXTRACTION_PROVIDER=demo
```

External production adapters for these three capabilities are **NOT CURRENTLY SUPPORTED**. Do not
describe their demo output as externally verified clinical processing.

## 4. Development versus production

Development may enable debug mode:

```dotenv
APP_ENV=development
APP_DEBUG=true
DATABASE_ECHO_SQL=false
```

Development can explicitly select demo providers and omit Blob/Redis only when persistent evidence
and asynchronous execution are not being exercised:

```dotenv
LLM_PROVIDER=demo
EMBEDDING_PROVIDER=demo
OCR_PROVIDER=demo
STT_PROVIDER=demo
TTS_PROVIDER=demo
```

Production must use:

```dotenv
APP_ENV=production
APP_DEBUG=false
DATABASE_ECHO_SQL=false
```

Production also requires `REDIS_URL`, `AZURE_STORAGE_CONNECTION_STRING`, fully configured Azure
LLM/embedding/STT/TTS settings, and Azure Document Intelligence. The following configuration must
fail closed and must never be worked around:

```dotenv
APP_ENV=production
APP_DEBUG=true
```

Verify configuration without printing secrets:

```bash
.venv/bin/python -c "from careintel.core.config import Settings; s=Settings(); print('CONFIG_OK'); print(f'APP_ENV={s.app_env}'); print(f'APP_DEBUG={s.app_debug}')"
```

Do not print `Settings.model_dump()`: it can expose sensitive values despite the use of `SecretStr`.

## 5. PostgreSQL and Supabase setup

Provision an external PostgreSQL database and place its async DSN in `DATABASE_URL`. For Supabase,
the template uses the direct database connection on port 5432 with `ssl=require`. Connection-mode
selection is an environment/operator decision; confirm it supports persistent backend connections
and Alembic DDL.

The migration identity must be allowed to create and alter tables, indexes, functions, triggers,
and the `vector` extension, or pgvector must already be enabled by the database administrator.
Alembic sets `search_path` to `public, extensions` for Supabase-compatible extension discovery.

The schema includes identity, consent, cases, evidence, processing/provenance, structuring,
knowledge/retrieval, AI drafts and policy decisions, review/handoff, async tasks, outboxes, and
append-only audit records. Do not create these tables manually.

## 6. Alembic migrations

Apply every pending migration to a fresh or existing database:

```bash
.venv/bin/alembic upgrade head
```

Verify the applied revision:

```bash
.venv/bin/alembic current
```

Verify that ORM metadata would not generate another migration:

```bash
.venv/bin/alembic check
```

The current repository head is **`0014`**. A healthy current database reports `0014 (head)`, and a
clean drift check reports `No new upgrade operations detected.`

The drift check may also emit Alembic's warning that the computed default on
`knowledge_chunks.fts_vector` cannot be modified. The current verified check still exits successfully
with no upgrade operations; do not hide a different warning or non-zero exit status.

Run migrations before starting API, worker, or dispatcher processes for a new release. Never edit an
already-applied migration, delete migration history, reset production data, or use `alembic stamp`
to conceal drift. Create a new migration for a demonstrated schema change.

Migration `0010` deliberately deletes old demo embeddings while changing the vector dimension from
768 to 1,536. Review historical migrations before applying them to a database created from an older
release.

## 7. Redis, Celery, and transactional outboxes

The async path is:

```text
application transaction
  -> PostgreSQL case/evidence outbox
  -> outbox dispatcher
  -> Redis broker
  -> Celery worker
  -> durable async task and business-state updates in PostgreSQL
```

Start a worker from the repository root:

```bash
.venv/bin/celery -A careintel.workers.celery_app:celery_app worker \
  --loglevel=INFO \
  -Q careintel_default,careintel_processing,careintel_retrieval,careintel_ai,careintel_workflow
```

Start the transactional-outbox dispatcher as a separate long-running process:

```bash
.venv/bin/python -m careintel.workers.outbox_runner --interval 2
```

Run one bounded dispatch pass for diagnosis or controlled operation:

```bash
.venv/bin/python -m careintel.workers.outbox_runner --once
```

Verify that at least one worker responds:

```bash
.venv/bin/celery -A careintel.workers.celery_app:celery_app inspect ping --timeout 10
```

Stop foreground worker and dispatcher processes with `Ctrl-C` and allow graceful shutdown. In
production, supervision and graceful service termination are **REQUIRES MANUAL CONFIGURATION**.

Celery uses late acknowledgement, rejects work when a worker is lost, uses prefetch multiplier 1,
and applies configured soft/hard time limits. Business tasks claim durable PostgreSQL rows and treat
duplicate delivery idempotently.

Celery Beat is not configured. Automatic scheduling of the registered stale-task recovery task is
**REQUIRES MANUAL CONFIGURATION**. Do not add a second queue system or treat Redis as authoritative
workflow state.

## 8. Azure and external services

### Azure Blob Storage

The API verifies or creates the configured private container during startup. Startup uses
`DEPENDENCY_CONNECT_TIMEOUT_SECONDS` and fails if the container cannot be verified. Grant the
runtime identity/connection string the minimum data-plane permissions needed for container
verification, object upload/download/delete, and read-only SAS generation.

### Azure OpenAI-compatible resource

The current adapters use configured deployments for:

- strict JSON-schema advisory LLM output;
- 1,536-dimensional embeddings;
- standard STT or diarized STT;
- MP3 TTS.

Provider failure is surfaced as failed processing/AI/task state. There is no fabricated production
fallback when `APP_ENV=production`; production Settings reject demo/unconfigured selectors.

### Azure Document Intelligence

The OCR adapter uses `prebuilt-layout` by default and persists provider-returned pages, regions, and
table information. The synchronous Azure SDK operation is isolated with `asyncio.to_thread`.

### Current external-service limitations

- Real malware/content scanning is **NOT CURRENTLY SUPPORTED**.
- A production handoff delivery provider is **NOT CURRENTLY SUPPORTED**. The worker refuses the demo
  handoff provider in production and records failure rather than fake delivery.
- External language-detection, translation, and extraction adapters are **NOT CURRENTLY SUPPORTED**.
- The repository does not provision Azure, Supabase, or Redis resources. Resource provisioning is
  **REQUIRES MANUAL CONFIGURATION**.

## 9. Infrastructure verification

Run the synthetic infrastructure verifier after migrations and before starting production traffic:

```bash
.venv/bin/python scripts/verify_infra.py
```

It checks:

- PostgreSQL connectivity and agreement with the repository Alembic head;
- pgvector extension availability;
- the `vector(1536)` embedding column;
- the HNSW cosine index;
- Redis `PING`;
- Celery broker connectivity;
- Azure Blob synthetic upload, existence, download integrity, SAS generation, missing-object
  handling, and cleanup.

This script writes one uniquely named synthetic Blob and deletes it. It does not verify Celery worker
execution and prints `worker_execution: NOT VERIFIED by this check`.

Optional real-provider smoke checks call billable/external Azure APIs:

```bash
.venv/bin/python scripts/verify_providers.py --only llm
.venv/bin/python scripts/verify_providers.py --only embedding
.venv/bin/python scripts/verify_providers.py --only ocr
.venv/bin/python scripts/verify_providers.py --only tts
.venv/bin/python scripts/verify_providers.py --only stt
.venv/bin/python scripts/verify_providers.py --only diarization
```

Run only the capabilities you intend to verify. The diarization fixture is single-speaker and cannot
establish multi-speaker diarization quality.

## 10. Start the FastAPI application

Development:

```bash
.venv/bin/uvicorn careintel.main:app --reload --host 127.0.0.1 --port 8000
```

Production process command:

```bash
.venv/bin/uvicorn careintel.main:app --host 0.0.0.0 --port 8000
```

Do not use `--reload` in production. `APP_HOST` and `APP_PORT` are application settings but the
current repository does not wrap Uvicorn to consume them as CLI bind arguments; pass the actual host
and port explicitly.

The repository does not include Gunicorn, systemd units, deployment manifests, TLS termination, or
a production process manager. Those are **REQUIRES MANUAL CONFIGURATION**. Expose Uvicorn directly
only in a trusted environment; use an operator-approved HTTPS/reverse-proxy boundary in production.

Interactive API documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/api/docs`
- ReDoc: `http://127.0.0.1:8000/api/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/api/openapi.json`

## 11. Liveness and readiness

Liveness checks only whether the process can handle a request:

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health/live
```

Expected body:

```json
{"status":"ok"}
```

Readiness checks PostgreSQL, Redis, and Blob Storage concurrently with bounded probe timeouts:

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health/ready
```

A ready response is HTTP 200 with this shape:

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "blob_storage": "ok"
  },
  "latency_ms": 0.0
}
```

`latency_ms` is measured and will vary. Any unavailable required dependency produces HTTP 503 with
`status: not_ready`. Liveness does not prove dependencies, migrations, a running Celery worker, or a
running outbox dispatcher.

## 12. Required startup order

For a fresh environment:

1. Provision external PostgreSQL/pgvector, Redis, Azure Blob, Azure OpenAI deployments, and Azure
   Document Intelligence.
2. Clone the repository and run `uv sync --all-extras --frozen`.
3. Inject secrets and configuration; keep `APP_ENV=production` and `APP_DEBUG=false` in production.
4. Run the secret-safe `Settings` check from section 4.
5. Apply migrations with `.venv/bin/alembic upgrade head`.
6. Run `.venv/bin/alembic current` and `.venv/bin/alembic check`.
7. Run `.venv/bin/python scripts/verify_infra.py`.
8. Start the Celery worker.
9. Confirm the worker with Celery `inspect ping`.
10. Start the outbox dispatcher.
11. Start FastAPI without reload.
12. Verify liveness and readiness.
13. Bootstrap the first administrator only if no ADMIN assignment exists.
14. Log in and verify `/api/v1/auth/me`.

For normal restarts after the database is initialized, repeat configuration validation, migration
application/checks, worker, dispatcher, API, and health checks. Do not rerun first-admin bootstrap.

## 13. First production administrator

The first administrator is provisioned only through the CLI:

```bash
.venv/bin/python -m scripts.bootstrap_admin
```

This is not public registration; there is no `/register` endpoint. The command:

- requires `APP_ENV=production`;
- accepts no CLI arguments;
- prompts for email and display name;
- uses non-echoing terminal input for password and confirmation;
- requires a password of at least 12 characters and no more than 72 UTF-8 bytes;
- requires the operator to type `SYSTEM-WIDE` explicitly;
- displays only non-secret values and requires `y`/`yes` confirmation;
- hashes the password with bcrypt cost 12;
- creates an active, verified user;
- assigns the existing `admin` role with `facility_id = NULL`;
- ensures the existing `manage:users` and `manage:system` permissions are mapped to that role;
- creates an append-only `ADMIN_BOOTSTRAPPED` audit event with system/bootstrap provenance;
- commits user, role assignment, permission mapping, and audit atomically;
- locks the admin role and refuses when any ADMIN assignment already exists;
- refuses duplicate email, missing role/permissions, invalid input, or database failure without a
  partial account.

Only system-wide first-admin scope is currently supported. Facility-specific bootstrap is **NOT
CURRENTLY SUPPORTED**. The ADMIN role does not automatically bypass authorization and does not gain
clinical/reviewer permissions merely because it is administrative.

Never create the first administrator with ad-hoc SQL. `scripts/seed_dev_admin.py` is development-
only, refuses `APP_ENV=production`, and must not be used for production provisioning.

## 14. First-admin example

```text
CareIntel Production Admin Bootstrap

Email: admin@example.com
Display name: CareIntel Administrator
Password: <entered securely; not echoed>
Confirm password: <entered securely; not echoed>
Scope (type SYSTEM-WIDE to select the supported bootstrap scope): SYSTEM-WIDE

Admin account prepared.
Email: admin@example.com
Role: admin
Scope: system-wide
User ID: <generated UUID>
Create this administrator? [y/N] y
```

Do not put the password in a command argument, shell history, deployment log, or ticket.

## 15. Login and authenticated API verification

The login contract is:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "YOUR_PASSWORD"
}
```

For a disposable local shell, substitute placeholders without committing or sharing the command:

```bash
curl --fail --silent --show-error \
  --request POST \
  --header 'Content-Type: application/json' \
  --data '{"email":"admin@example.com","password":"YOUR_PASSWORD"}' \
  http://127.0.0.1:8000/api/v1/auth/login
```

The response contains `access_token` and `token_type: bearer`. Do not log or commit the token. Use it
to verify the authenticated profile:

```bash
curl --fail --silent --show-error \
  --header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  http://127.0.0.1:8000/api/v1/auth/me
```

The profile returns the user UUID, active state, roles, and permissions. Revoke the current token:

```bash
curl --fail --silent --show-error \
  --request POST \
  --header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  http://127.0.0.1:8000/api/v1/auth/logout
```

Logout returns HTTP 204. Reusing the revoked token must fail. There is no refresh-token endpoint and
no public registration endpoint.

## 16. Development workflow

Use a separate test database. Never point integration or E2E tests at production. `tests/conftest.py`
forces `APP_ENV=testing`, but an existing `.env` can still provide `DATABASE_URL`; explicitly set a
safe test DSN before live-database tests.

Common checks:

```bash
.venv/bin/ruff format --check src/careintel tests scripts
.venv/bin/ruff check src/careintel tests scripts
.venv/bin/mypy src/careintel
.venv/bin/python -m pytest tests/unit tests/api
```

Do not mechanically reformat already-applied migration files as routine cleanup. The historical
`0007`-`0010` revisions do not satisfy the current Ruff style configuration, but migration history
must remain stable. Review new migration files before application and validate schema state with
Alembic rather than rewriting applied revisions to make a formatting command green.

Live integration tests require a disposable migrated PostgreSQL database:

```bash
APP_ENV=testing DATABASE_URL=postgresql+asyncpg://TEST_USER:TEST_PASSWORD@TEST_HOST:5432/TEST_DATABASE \
  .venv/bin/python -m pytest tests/integration tests/e2e -m integration
```

Do not run release/provider scripts repeatedly: they may call external services, consume quota, or
create synthetic records/blobs. Read each script before running it against a shared environment.

`scripts/seed_dev_admin.py` is guarded against production, but its current implementation constructs
its engine from the deliberately masked `database_url_safe()` value. Reliable development-admin
provisioning through that legacy script is therefore **NOT CURRENTLY SUPPORTED** for credentialed
external databases. Do not use it in production, and do not work around it with direct SQL. Use
isolated test fixtures for automated tests; a future change must repair and test the development
seed path before it is documented as an executable onboarding command.

## 17. Production operating procedure

For each deployment:

1. Deploy the exact reviewed source and locked dependencies.
2. Inject configuration through the deployment secret mechanism.
3. Validate `Settings` without dumping secrets.
4. Apply and verify migrations once using a migration-capable identity.
5. Run infrastructure verification during a controlled preflight window.
6. Start or roll the Celery worker and verify it responds.
7. Start the outbox dispatcher as a singleton-safe supervised process. Multiple dispatchers use
   PostgreSQL locking, but operational process count remains a deployment decision.
8. Start or roll the FastAPI process.
9. Require liveness and readiness success before routing traffic.
10. Check logs for bounded startup/provider failures without exposing payloads.

The repository emits structured JSON logs and propagates `X-Correlation-ID`. It does not include a
Prometheus `/metrics` endpoint, distributed tracing exporter, alerting rules, dashboards, or log
shipping. Those capabilities are **NOT CURRENTLY SUPPORTED** by repository code or **REQUIRES
MANUAL CONFIGURATION** at the platform layer.

Backups, point-in-time recovery, Redis durability policy, Azure retention/versioning, key rotation,
network restrictions, and disaster-recovery procedures are **REQUIRES MANUAL CONFIGURATION**.

## 18. Troubleshooting

### `app_debug must be False when app_env is 'production'`

The active shell or `.env` has production plus debug enabled. Keep the validator. Set:

```bash
export APP_ENV=production
export APP_DEBUG=false
```

Check both the shell and `.env`; process environment values take precedence.

### `DATABASE_URL must use the asyncpg driver scheme`

Change the scheme to `postgresql+asyncpg://` and URL-encode credential characters. Do not place the
DSN in `alembic.ini`; Alembic loads it through `Settings`.

### Production Settings rejects missing infrastructure/providers

Production requires Redis, Azure Blob, Azure OpenAI selectors/key, and Azure Document Intelligence.
Demo fallback is intentionally rejected for LLM, embeddings, OCR, STT, and TTS.

### Alembic cannot create `vector`

Ask the database administrator to enable pgvector or grant the migration identity permission to
create the extension. Do not remove the migration or replace pgvector.

### Application startup waits for or fails Blob initialization

Startup verifies/creates the container and is bounded by `DEPENDENCY_CONNECT_TIMEOUT_SECONDS`.
Check the Blob connection, container permission, network route, and timeout. Do not hide the failure.

### Readiness returns 503

Inspect the `checks` object to identify `database`, `redis`, or `blob_storage`. Each probe is bounded
by `READINESS_TIMEOUT_SECONDS`. Liveness may remain 200 while readiness is 503.

### Celery reports no responding workers

Confirm the worker process is running with the documented app path and queues, and that every
process sees the same `REDIS_URL`. `verify_infra.py` proves broker connectivity only, not worker
execution.

### Outbox rows stay pending

The Celery worker does not poll PostgreSQL outboxes. Start
`careintel.workers.outbox_runner` separately and inspect its logs. Confirm the event type is one of
the dispatcher's supported task mappings.

### Uploaded evidence remains `STORED`

This is expected with the current `NoOpScanner`: it returns `PENDING`. Real content scanning is
**NOT CURRENTLY SUPPORTED**. Do not force evidence to `READY` by editing the database.

### First-admin bootstrap refuses

The command refuses when any ADMIN assignment exists, the email already exists, required migration
data is missing, the scope is not explicitly `SYSTEM-WIDE`, or the password is outside 12 characters
to 72 UTF-8 bytes. Use normal authorized administration for later accounts; do not bypass the guard
with SQL.

### CORS configuration fails to parse

Use JSON list syntax:

```dotenv
CORS_ALLOWED_ORIGINS=["https://app.example.com","https://ops.example.com"]
```

### Provider verification fails

Confirm the endpoint, deployment, API version, key, network access, and provider selector. A class
importing successfully is not proof that the external deployment exists. Run only the corresponding
`verify_providers.py --only ...` check and treat unavailable providers as not verified.

### Audit UPDATE or DELETE fails

This is expected. Migration `0013` installs an append-only database trigger on `audit_logs`. Do not
disable it or mutate historical audit records.

## 19. Minimal command sequence

Development API without async execution:

```bash
uv sync --all-extras --frozen
cp .env.example .env
# Edit .env with a non-production database, secrets, and explicit demo providers.
.venv/bin/alembic upgrade head
.venv/bin/alembic current
.venv/bin/uvicorn careintel.main:app --reload --host 127.0.0.1 --port 8000
```

Production service set after external resources and secrets are configured:

```bash
.venv/bin/alembic upgrade head
.venv/bin/alembic current
.venv/bin/alembic check
.venv/bin/python scripts/verify_infra.py

# Process 1
.venv/bin/celery -A careintel.workers.celery_app:celery_app worker \
  --loglevel=INFO \
  -Q careintel_default,careintel_processing,careintel_retrieval,careintel_ai,careintel_workflow

# Process 2
.venv/bin/python -m careintel.workers.outbox_runner --interval 2

# Process 3
.venv/bin/uvicorn careintel.main:app --host 0.0.0.0 --port 8000
```

After all three processes are running, check liveness, readiness, worker response, authentication,
and the authenticated profile. Run `scripts.bootstrap_admin` only once on a database with no ADMIN
assignment.

## 20. Docker Deployment

This section covers the container-based deployment of CareIntel using the `Dockerfile` and
`compose.yaml` files in the repository root. All external services (PostgreSQL/Supabase, Redis,
Azure Blob Storage, Azure AI) remain external managed services. No local infrastructure containers
are started.

**No default administrator account is created automatically by the image build or container
startup.** Administrator provisioning requires an explicit, interactive step documented in
section 13 of this guide.

### 20.1 Prerequisites

- **Docker 24+** and **Docker Compose v2.20+** (`docker compose` as a plugin, not `docker-compose`).
- All external services provisioned and reachable: PostgreSQL/Supabase, Redis, Azure Blob Storage,
  Azure OpenAI-compatible deployments, Azure Document Intelligence.
- The `DATABASE_URL` must use the `postgresql+asyncpg://` scheme; see section 3 for details.
- If the PostgreSQL host resolves only to IPv6 and the container host lacks IPv6 routing, use the
  Supabase Session Pooler (port 5432) which resolves to IPv4:
  `postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?ssl=require`

### 20.2 Environment configuration

Copy the template to `.env` and fill in all values:

```bash
cp .env.example .env
chmod 600 .env
```

`.env` is read by Docker Compose from the `env_file` directive. It is excluded from the Docker
build context by `.dockerignore` and is never copied into any image layer.

**Required in every environment:**

```dotenv
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE?ssl=require
SECRET_KEY=<long-random-string>
JWT_SECRET_KEY=<different-long-random-string>
```

**Required in production (`APP_ENV=production`):**

```dotenv
APP_ENV=production
APP_DEBUG=false
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
REDIS_URL=redis://default:PASSWORD@HOST:PORT
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.openai.azure.com/
AZURE_LLM_DEPLOYMENT=<deployment>
LLM_PROVIDER=azure_openai
EMBEDDING_PROVIDER=azure_openai
STT_PROVIDER=azure_openai_diarize
TTS_PROVIDER=azure_openai
OCR_PROVIDER=azure_document_intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://YOUR_RESOURCE.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=<key>
```

In a deployed environment (staging/production), prefer injecting secrets through the platform's
secret manager or environment injection rather than copying a `.env` file. Never commit `.env`.

Validate configuration without printing secrets (same check as section 4):

```bash
docker run --rm --env-file .env careintel:latest \
  python -c "from careintel.core.config import Settings; s=Settings(); print('CONFIG_OK'); print(f'APP_ENV={s.app_env}')"
```

### 20.3 Build the image

```bash
docker build -t careintel:latest .
```

The Dockerfile uses a two-stage build:

1. **Builder stage**: installs `uv`, resolves all production dependencies from the committed
   `uv.lock`, and builds the `careintel` package.
2. **Runtime stage**: `python:3.12-slim` base with only `libmagic1` as an OS-level dependency,
   non-root user (`appuser`, UID 1001), venv and source copied from the builder.

Build arguments are not used. No secrets appear in any layer.

To rebuild after dependency changes (updates `uv.lock`):

```bash
docker build --no-cache -t careintel:latest .
```

### 20.4 Database migrations

**Run migrations explicitly before starting or updating services.** Migrations are never run
automatically on API or worker startup. Never run migrations from multiple containers concurrently.

```bash
# Apply all pending migrations
docker compose run --rm migrate

# Verify the applied revision
docker compose run --rm migrate alembic current

# Verify schema drift (no new operations expected after migration)
docker compose run --rm migrate alembic check
```

The `migrate` service in `compose.yaml` runs `alembic upgrade head` and exits. It uses the same
image and environment as the API and worker, ensuring migration context is identical to production.

A healthy database after migration reports `0014 (head)` from `alembic current` and
`No new upgrade operations detected` from `alembic check`.

### 20.5 Start the services

Start all three application processes:

```bash
docker compose up -d api worker outbox
```

Or start them individually:

```bash
docker compose up -d api
docker compose up -d worker
docker compose up -d outbox
```

**Service roles:**

| Service | Command | Role |
|---------|---------|------|
| `api` | `uvicorn careintel.main:app --host 0.0.0.0 --port 8000 --workers 1` | FastAPI HTTP server |
| `worker` | `celery -A careintel.workers.celery_app:celery_app worker ...` | Async task execution |
| `outbox` | `python -m careintel.workers.outbox_runner --interval 2` | PostgreSQL outbox dispatcher |

All three services must be running for full async workflow execution. The outbox dispatcher is a
separate required process — the Celery worker does not poll the PostgreSQL outbox tables.

### 20.6 Health verification

```bash
# Liveness: process is alive
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health/live

# Readiness: all dependencies are reachable
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health/ready

# Celery worker is responding
docker compose exec worker \
  celery -A careintel.workers.celery_app:celery_app inspect ping --timeout 10
```

Expected liveness response: `{"status":"ok"}`

Expected readiness response (HTTP 200):
```json
{"status":"ready","checks":{"database":"ok","redis":"ok","blob_storage":"ok"},"latency_ms":0.0}
```

A readiness 503 with a specific check set to `"error"` identifies the failing dependency.

### 20.7 Logs and troubleshooting

```bash
# Follow all service logs
docker compose logs -f

# Follow a specific service
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f outbox

# Check running containers
docker compose ps
```

Logs are emitted as structured JSON to stdout. The `X-Correlation-ID` header propagates through
all API logs for request tracing.

**Common issues:**

- `DATABASE_URL must use the asyncpg driver scheme`: change scheme to `postgresql+asyncpg://`.
- `AZURE_STORAGE_CONNECTION_STRING must be set in production`: set the variable before starting.
- `Production provider configuration must use fully configured external adapters`: all Azure AI
  provider variables and the API key must be set when `APP_ENV=production`.
- Readiness returns 503 for `database`: verify `DATABASE_URL` and network connectivity from the
  container to the database host. On IPv4-only hosts, use the Supabase Session Pooler address.
- `Outbox rows stay pending`: confirm the `outbox` service is running. The Celery worker does not
  dispatch from the PostgreSQL outbox.

### 20.8 Administrator bootstrap (first deployment only)

Run only once, on a database that has no ADMIN role assignment:

```bash
docker compose run --rm \
  -e APP_ENV=production \
  api \
  python -m scripts.bootstrap_admin
```

This command is interactive and prompts for email, display name, password, and a scope
confirmation token. The password is not echoed and must not be passed as a command-line argument.
See section 13 for the complete bootstrap contract and section 14 for an example session.

**No administrator account is created during image build or service startup.**

### 20.9 Shutdown and update procedure

```bash
# Stop all services gracefully
docker compose down

# Stop and remove volumes (if any were created)
docker compose down -v

# Rebuild and redeploy
docker build -t careintel:latest .
docker compose run --rm migrate           # apply new migrations
docker compose up -d api worker outbox    # restart services
```

The Celery worker has a `stop_grace_period: 370s` (just past the hard task time limit of 360s)
to allow in-flight tasks to complete before the container is forcefully terminated.

### 20.10 External service configuration reference

All external services are configured through environment variables, not through container
definitions. See section 3 for the full variable reference. Summary:

| Service | Key variables |
|---------|--------------|
| PostgreSQL/Supabase | `DATABASE_URL` |
| Redis | `REDIS_URL` |
| Azure Blob Storage | `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_STORAGE_CONTAINER` |
| Azure OpenAI | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, deployment names |
| Azure Document Intelligence | `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`, `AZURE_DOCUMENT_INTELLIGENCE_KEY` |

### 20.11 Production secret management

Docker Compose `env_file` is suitable for development. For production:

- **Azure**: use Azure Key Vault with the container's managed identity or inject secrets via
  Azure Container Apps / AKS secret volumes.
- **AWS**: use AWS Secrets Manager with ECS task definitions or Kubernetes External Secrets.
- **Kubernetes**: mount secrets as environment variables from Kubernetes Secret objects; do not
  use ConfigMaps for sensitive values.

Never commit `.env` with real credentials. Never use Docker build arguments for secrets.
Never log or print environment variables in health checks or startup output.

