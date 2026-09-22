# CareIntel Release Evidence

## 1. Release Scope

This report records the final hardening and verification performed against the current CareIntel repository. It covers repository/build integrity, PostgreSQL and pgvector, Azure Blob Storage, Redis/Celery connectivity, configured Azure AI providers, authentication and selected security controls, failure behavior, the available synthetic E2E path, audit integrity, observability, and documentation.

- Docker was explicitly excluded. No Docker files or container infrastructure were added.
- The existing FastAPI, application/domain service, PostgreSQL/pgvector, Azure Blob, Redis/Celery, Azure AI, transactional outbox, and persisted state-machine architecture was preserved.
- All created or executed fixtures used synthetic data. No real patient data or PHI was used.
- Live checks used the configured external Supabase PostgreSQL, pgvector, Redis, Azure Blob, Azure OpenAI, and Azure Document Intelligence resources where stated.
- No local PostgreSQL or Redis was installed.
- No external resource was reset, truncated, dropped, or destructively modified.

This is evidence for the repository state described below. It is not a compliance certification or a claim of comprehensive security.

## 2. Repository State

| Item | Observed value |
|---|---|
| Branch | `E2E` |
| Base commit | `c3fdd50aa8bb27e092dd244abf5da75ea3b98bd9` |
| Working tree | Modified by this hardening phase; not committed |
| Package version | `0.1.0` |
| Python | `3.12.3` |
| Alembic head | `0010` |
| Verification date | `2026-09-23` (Asia/Kolkata) |
| Evidence snapshot time | `2026-09-23T01:26:25+05:30` |
| Dependency lock | `uv lock --check`: PASS, 100 packages resolved |
| Package build | `UV_CACHE_DIR=/tmp/careintel-uv-cache uv build --out-dir /tmp/careintel-release-build`: PASS after network access was permitted; sdist and wheel built in `/tmp` |

The initial package build attempt was blocked by sandbox DNS restrictions. The required external build dependency was then fetched with approved network access and the same build completed successfully.

### Static and test results

| Verification | Actual command | Result |
|---|---|---|
| Lint | `.venv/bin/ruff check src/careintel tests scripts test_env.py test_celery.py` | PASS |
| Active-code formatting | `.venv/bin/ruff format --check src/careintel tests scripts test_env.py test_celery.py` | PASS; 287 files formatted |
| Whole-repository formatting | `.venv/bin/ruff format --check .` | FAIL; five historical applied Alembic files would be reformatted |
| Type checking | `.venv/bin/mypy src/careintel` | PASS; 230 source files |
| Byte compilation | `.venv/bin/python -m compileall -q src/careintel tests scripts` | PASS |
| Primary pytest/coverage suite | `.venv/bin/python -m pytest --cov=careintel --cov-report=term-missing --cov-report=json:coverage.json` | 192 passed, 3 skipped; 71.92% coverage; zero failed |
| Live integration run | `.venv/bin/python -m pytest tests/integration -q --run-integration` | 4 passed |
| Live synthetic E2E run | `.venv/bin/python -m pytest tests/e2e/test_golden_path.py -q --run-e2e` | 1 passed; scope is partial and described below |
| Diff whitespace | `git diff --check` | PASS |

The five whole-repository format failures are `migrations/env.py` and migrations `0007` through `0010`. Applied migration history was not mechanically rewritten solely to make the formatter green.

## 3. Infrastructure Verification

### PostgreSQL / Supabase

| Check | Method | Result |
|---|---|---|
| Connectivity | `scripts/verify_infra.py` | PASS |
| Applied revision | `.venv/bin/alembic current` | PASS: `0010 (head)` |
| Static head | `.venv/bin/alembic heads` | PASS: `0010 (head)` |
| ORM/schema drift | `.venv/bin/alembic check` | PASS: no new upgrade operations detected |
| pgvector extension | `scripts/verify_infra.py` | PASS |
| Vector column | Live metadata query | PASS: `vector(1536)` |
| Vector index/operator class | Live metadata query | PASS: HNSW cosine index |
| Database probe latency | Single infrastructure probe | 16,279.93 ms |

ORM registration, timestamp/default alignment, the vector type, generated full-text column, GIN index, and HNSW metadata were corrected to match the applied schema. No applied migration was edited and no new migration was required after `alembic check` reached a clean result.

Limitation: existing migration `0010` rebuilds the prior embedding column/index when first applied. It was already the live head and was not re-executed during this phase.

### Azure Blob Storage

`scripts/verify_infra.py` executed against the real configured adapter using a synthetic object.

| Check | Result |
|---|---|
| Container access | PASS |
| Synthetic upload | PASS |
| Download | PASS |
| Byte integrity | PASS |
| Time-limited access URL generation | PASS |
| Missing-object behavior | PASS |
| Cleanup | PASS |
| Probe duration | 2,866.46 ms |

The adapter now closes its client during application shutdown. Logs do not include object keys, signed URLs, connection strings, or raw provider exceptions.

The latest full runtime readiness rerun stalled during external Blob initialization and was operator-terminated after approximately 150 seconds without producing a readiness response. An earlier same-day runtime probe passed database, Redis, and Blob readiness. Therefore repeatable startup under external-service delay is PARTIAL, and startup timeout behavior remains a release limitation.

### Redis

| Check | Result |
|---|---|
| Direct ping | PASS; 396.65 ms |
| Celery broker connection | PASS; 418.18 ms |
| Safe payload review | PARTIAL; task boundaries use identifiers/metadata, but no exhaustive broker inspection was performed |
| Interruption/recovery drill | NOT VERIFIED; interruption of the shared external service was not safe in this environment |

### Celery

- A real `pool=solo` Celery worker was started against the configured Redis broker.
- `celery inspect ping` returned one online worker and `pong`.
- The worker was then stopped with a warm operator shutdown.
- This verifies worker/broker control-plane connectivity, not successful execution of the incomplete CareIntel business task bodies.
- Task idempotency, completed-duplicate behavior, stale recovery, and retry exhaustion were executed as unit tests.
- Processing, retrieval, AI, and workflow task bodies now persist explicit `FAILED` state and raise `NOT_IMPLEMENTED`; they no longer sleep and report false success.

Business task execution, hosted outbox dispatch, outbox replay, crash/restart recovery, and bounded live provider retry are NOT VERIFIED. The outbox dispatcher also retains a dispatch-before-commit race and has no continuously hosted runner. These are release blockers.

## 4. AI Provider Verification

`scripts/verify_providers.py` executed real configured Azure provider calls. No provider credentials or full provider responses were printed or retained.

| Provider / deployment | Purpose | Verification | Result | Observed latency |
|---|---|---|---|---:|
| Azure OpenAI / `gpt-5.6-luna` | Structured LLM | Valid structured synthetic response | PASS | 2,146.95 ms |
| Azure OpenAI / `gpt-5.6-luna` | Injection resistance at provider boundary | Combined adversarial input was blocked by provider content filtering | PASS for this fixture | 2,440.28 ms |
| Azure OpenAI / `text-embedding-3-small` | Embedding | Nonempty 1,536-dimension vector | PASS | 1,277.43 ms |
| Azure OpenAI / `tts-hd` | Speech generation | Synthetic audio generated | PASS | 3,586.99 ms |
| Azure OpenAI / configured STT deployment | Transcription | Generated synthetic audio produced nonempty transcript | PASS | 3,429.73 ms |
| Azure OpenAI / configured diarization deployment | Speaker segmentation | Single-speaker fixture returned no speaker labels | NOT VERIFIED | 4,292.17 ms |
| Azure Document Intelligence / `prebuilt-layout` | OCR | Native synthetic PDF returned text and page provenance | PASS for native-PDF fixture | 5,804.76 ms |

The LLM adapter was corrected to use a configurable API version that supports the existing structured-output path. Provider selection, endpoint/deployment configuration, authentication, structured schema handling, and sanitized error behavior were exercised by the probe.

The following were not executed and remain NOT VERIFIED: malformed live provider response, reproducible provider rate limiting, provider timeout recovery, multi-speaker diarization, noisy/silent/code-switched audio, Hindi/Odia fixtures, scanned/table/poor-quality/unreadable OCR fixtures, and an end-to-end application workflow consuming these provider outputs.

Production configuration now fails closed when the wired LLM, embedding, OCR, STT, or TTS capability is configured for a demo adapter or lacks required external credentials. Demo adapters remain available in development and testing.

## 5. OCR / STT / Diarization / TTS

### OCR

Native-PDF OCR, extracted text presence, page provenance, persistence-capable result structure, and original Blob preservation were exercised. No table was present in the executed fixture, so table provenance is NOT VERIFIED. The broader required document matrix is NOT VERIFIED.

### STT and diarization

Synthetic TTS audio was transcribed through the real Azure adapter. Transcript presence and the adapter result structure were verified. The only diarization fixture was single-speaker and returned no speaker labels; multi-speaker diarization is NOT VERIFIED.

### TTS application path

`scripts/verify_tts_api.py` exercised:

`POST API route -> authorization dependency -> application speech service -> Azure TTS adapter -> audit call -> binary response`

| Check | Result |
|---|---|
| Missing JWT rejected | PASS |
| Authorized route | PASS, using a synthetic dependency override for identity |
| Nonempty audio body | PASS |
| Audio content type | PASS |
| End-to-end probe latency | 16,239.49 ms |

Actual JWT/session behavior was verified separately by the live authentication probe.

## 6. Golden E2E Result

Status: **FAIL for the required complete golden path; PARTIAL for the executable repository scenario.**

The live synthetic E2E test passed and asserted persisted state for:

1. synthetic administrator context;
2. active consent;
3. case creation;
4. case state in PostgreSQL;
5. durable case outbox event;
6. case audit record.

It uses dependency overrides/fake providers and ends after case creation/outbox/audit. It does not authenticate through the public login route and does not execute encounter creation, evidence upload, processing, OCR/STT persistence, extraction, timeline, missing-information evaluation, hybrid retrieval, AI drafting, reviewer approval, escalation, referral sending, recipient acknowledgement, or final audit reconstruction.

No encounter API exists. The incomplete structuring, review, escalation, referral, and handoff HTTP paths now return explicit `501 NOT_IMPLEMENTED` rather than static success. There is no public complete knowledge/retrieval/AI workflow. Accordingly, HTTP success and the partial E2E test are not treated as evidence for the requested full workflow.

## 7. Security Verification

| Security area | Test | Result | Evidence |
|---|---|---|---|
| Authentication | Missing/malformed/expired/forged signature/wrong issuer/wrong audience JWT | PASS | Unit/API security suite and runtime probe |
| Live authentication | Wrong password, token issue, JWT profile load, logout, replay after revocation | PASS | `scripts/verify_auth_live.py` |
| Live test identity cleanup | Synthetic account deactivated | PASS | `scripts/verify_auth_live.py` |
| Authorization | Permission and role rejection | PASS for tested cases | Unit/API security suite |
| Facility boundary | Missing or mismatched facility mapping denied | PASS | Auth policy and case service tests |
| Cross-object BOLA | Case/evidence selected paths tested | PARTIAL | No complete draft/referral/audit cross-object matrix |
| RBAC | Unauthorized/insufficient roles | PARTIAL | Stale claims and every clinical/admin boundary not fully exercised |
| Consent | Missing, withdrawn, stale, purpose/version mismatch, cross-subject evidence consent | PASS for implemented paths | Consent/evidence tests |
| Upload | Traversal, extension, magic bytes, MIME mismatch, size/unsupported type | PARTIAL | No active-content, polyglot, decompression-abuse, or real scanner test |
| Production provider fallback | Demo/missing external provider configuration | PASS: rejected | `tests/unit/test_config.py` |
| Prompt injection | Patient/OCR/STT/knowledge/extracted input remains user data; combined live attack fixture | PARTIAL/PASS for fixtures | Structural unit tests and provider content-filter result |
| Secret/system prompt exposure | No exposure observed in executed fixtures | PARTIAL | Not an exhaustive adversarial evaluation |
| Workflow action injection | No arbitrary tool surface; incomplete workflow actions return 501 | PASS for exposed scaffold boundary | Architecture/API tests |
| Sensitive logging | Secret-safe logging and probe output review | PARTIAL | No full dynamic log/metric/trace leakage harness |
| Audit mutation | Direct SQL UPDATE and DELETE attempts | FAIL: database allowed both inside rollback-only transactions | `scripts/verify_audit_integrity.py` |
| Duplicate commands/tasks | Existing key, completed duplicate, stale task, retry exhaustion | PARTIAL | Unit tests; live duplicate delivery not executed |

Live authentication provisioned a random synthetic account without printing its password, token, or address. It verified wrong-password rejection, token issuance, role/permission hydration, logout revocation, replay rejection, and deactivation. This probe found and led to correction of a defect where JWT `iat`/`exp` claims were dropped before session persistence.

Facility-role mappings are now loaded into the request context, and an absent mapping no longer grants global facility access. Evidence intake verifies that consent belongs to the subject and matches the required purpose/version before persistence.

The application audit repository is append-only at its API boundary, but database-level immutability is not enforced. This report therefore does not claim immutable audit records.

## 8. Failure / Recovery Verification

| Scenario | Result |
|---|---|
| Placeholder worker false success | PASS: prevented by architecture regression test and explicit failed state |
| Duplicate durable task key | PASS in unit test; no duplicate record |
| Duplicate already-completed task | PASS in unit test; no repeated business effect |
| Stale task recovery | PASS in unit test; moved back to pending |
| Retry exhaustion | PASS in unit test; durable failed state |
| Missing Blob object | PASS in real adapter probe |
| Blob cleanup | PASS in real adapter probe |
| External Blob startup stall | OBSERVED; latest runtime probe did not complete and was terminated after about 150 seconds |
| Provider content-filter rejection | PASS: no fabricated LLM output |
| Outbox replay | NOT VERIFIED |
| Worker crash/restart during business task | NOT VERIFIED |
| Redis interruption | NOT VERIFIED; unsafe against shared external service |
| Database outage | NOT VERIFIED; destructive/disruptive drill not authorized |
| OCR/STT/TTS/LLM explicit outage | NOT VERIFIED as a live outage drill |
| Provider rate limit/timeout | NOT VERIFIED |

Provider and storage errors are sanitized to error type/category where corrected; no fallback clinical answer is invented. The application still lacks a bounded startup timeout around external Blob initialization, as demonstrated by the final readiness rerun.

## 9. Performance Measurements

These are raw, small-sample observations, not clinical or production SLAs.

### In-process API probe

An earlier successful same-day `scripts/verify_runtime.py` run issued 100 sequential in-process ASGI liveness requests:

| Metric | Observed value |
|---|---:|
| Mean | 0.365 ms |
| p50 | 0.348 ms |
| p95 | 0.453 ms |
| p99 | 0.612 ms |
| Readiness request | 11,819.46 ms |

This sample excludes network ingress, concurrency, realistic application work, and queue/provider work. It is too small and artificial for capacity conclusions. The latest repeat of the same runtime script did not complete due to the external Blob startup stall.

### External probe observations

Individual provider and infrastructure latencies are listed in sections 3 and 4. Queue wait, business worker execution time, complete evidence-processing time, reviewer delay, and full workflow duration were not measurable because the corresponding end-to-end path is incomplete.

## 10. Observability Verification

| Capability | Result |
|---|---|
| Structured JSON logging | PASS |
| Correlation ID propagation/response | PASS in API tests/runtime probe |
| Causation ID model support | PARTIAL; no full cross-worker live trace |
| Durable task/provider identifiers | PARTIAL; modeled but incomplete workflow |
| Health/liveness | PASS in earlier runtime probe |
| Readiness dependency checks | PASS once; latest rerun stalled before completion |
| OpenAPI generation | PASS: 44 paths |
| Registered method/path audit | PASS: 52 method/path keys, zero duplicates |
| Debug route audit | PASS in runtime probe |
| Secret/PHI-safe logs | PARTIAL; reviewed executed output and corrected raw exception/URL logging, but no exhaustive sink audit |
| Metrics/tracing backend | NOT VERIFIED; no complete exported telemetry path was demonstrated |

The misleading startup route count was removed because FastAPI lazy routers made the top-level count incomplete. The dedicated recursive route audit is the evidence source for route registration.

## 11. Requirement Gap Matrix

| ID | Category | Status | Evidence / limitation |
|---|---|---|---|
| A | Application startup | PARTIAL | Earlier lifespan pass; latest external Blob startup stalled |
| B | Configuration | PASS | Typed settings, secret wrappers, production fail-closed provider tests |
| C | Database | PASS | Live head, drift, schema, vector checks |
| D | Authentication | PASS | Unit/API matrix plus live login/logout/replay |
| E | Authorization | PARTIAL | Facility fix and selected BOLA tests; incomplete object matrix |
| F | Consent | PASS | Lifecycle and evidence-consent tests |
| G | Case lifecycle | PARTIAL | Create/history/transition services; only creation live E2E |
| H | Evidence lifecycle | PARTIAL | Integrity and consent hardening; no complete live processing path |
| I | Azure Blob | PASS | Real upload/download/integrity/SAS/missing/cleanup |
| J | OCR | PARTIAL | Real native PDF only |
| K | STT | PARTIAL | Real synthetic transcription; fixture matrix incomplete |
| L | TTS | PASS | Real provider and API-service-provider path |
| M | Extraction | PARTIAL | Internal/demo processing only; no live structured extraction E2E |
| N | Provenance | PARTIAL | Models/unit checks and OCR page provenance; no full lineage reconstruction |
| O | Timeline | PARTIAL | Internal structuring logic; public path is incomplete |
| P | Missing information | PARTIAL | Unit/service logic; public path is incomplete |
| Q | Retrieval | PARTIAL | Lexical/vector/fusion code and tests; no real case-to-draft E2E |
| R | Embeddings | PASS | Real 1,536-vector provider call and DB dimension match |
| S | pgvector | PASS | Live extension/column/index checks |
| T | AI provider | PARTIAL | Real structured call; application workflow incomplete |
| U | AI output validation | PARTIAL | Schema/provenance policy tests; full validation chain not E2E |
| V | Safety policy | PARTIAL | Provenance rule only; prohibited-clinical-content suite incomplete |
| W | Prompt injection | PARTIAL | Structural matrix plus one live combined fixture |
| X | Async workflow | FAIL | Business task bodies intentionally fail as not implemented |
| Y | Redis | PASS | Real ping and broker connection |
| Z | Celery | PARTIAL | Real worker ping; no successful business task |
| AA | Outbox | FAIL | Persistence verified; no hosted runner/replay and dispatch race remains |
| AB | Idempotency | PARTIAL | Durable task unit tests; live duplicate matrix incomplete |
| AC | Reviewer workflow | FAIL | HTTP boundary returns 501 |
| AD | Approval | FAIL | No executable public human approval path |
| AE | Escalation | FAIL | HTTP boundary returns 501 |
| AF | Referral | FAIL | HTTP boundary returns 501 |
| AG | Recipient acknowledgement | FAIL | No executable public completion path |
| AH | Audit | FAIL | Partial append-only application design; DB UPDATE/DELETE allowed |
| AI | Observability | PARTIAL | Logs/correlation/health present; no complete metrics/tracing evidence |
| AJ | Security | PARTIAL | Executed matrix has meaningful passes and material unverified areas |
| AK | Failure recovery | PARTIAL | Durable task unit recovery; live outage/replay drills incomplete |
| AL | E2E | FAIL | Only case/outbox/audit partial scenario is executable |
| AM | Documentation | PASS | README and environment example aligned with actual capabilities |
| AN | Release evidence | PASS | This report is based on executed results and explicitly records failures |

## 12. Release Gate Matrix

| Gate | Status | Requirement and evidence | Limitations |
|---|---|---|---|
| G0 — Repository / Build Integrity | PARTIAL | Active lint/format/type/compile/tests pass; lock and package build pass | Five applied migration files fail whole-tree format |
| G1 — Database / Persistence Integrity | PASS | Live `0010` head, clean Alembic drift, pgvector dimension/index, integration tests | Non-destructive verification only; existing 0010 deployment behavior noted above |
| G2 — Security / Authorization | PARTIAL | Live authentication, JWT matrix, facility denial, consent and upload controls | Incomplete cross-object/RBAC/upload/leakage matrices; no real scanner |
| G3 — Evidence / Processing / Provenance | PARTIAL | Blob integrity, OCR/STT provider checks, evidence validation | No complete processing pipeline or broad fixture matrix |
| G4 — Retrieval / AI / Safety | PARTIAL | Real embedding/LLM calls, vector match, structural injection tests | Retrieval/application E2E absent; deterministic safety policy incomplete |
| G5 — Async Workflow / Recovery | FAIL | Redis/Celery control plane and unit recovery work | Business workers/outbox runner/replay not operational; dispatch race |
| G6 — Human Review / Handoff / Audit | FAIL | Models/state machines exist and false HTTP success was removed | Review/approval/referral/acknowledgement unavailable; audit DB mutable |
| G7 — E2E / Operational / Documentation | FAIL | Partial E2E, docs, OpenAPI, health evidence exist | Required complete golden path absent; latest readiness stalled |

## 13. Known Limitations

1. The complete CareIntel workflow is not executable end to end.
2. There is no encounter API.
3. Structuring, reviewer, escalation, referral, handoff, and acknowledgement APIs are incomplete and return `501 NOT_IMPLEMENTED`.
4. Processing, retrieval, AI, and workflow Celery business bodies explicitly fail rather than perform the planned work.
5. The transactional outbox lacks a hosted dispatcher/replay process and dispatch occurs before its status commit.
6. The no-op content scanner never declares uploaded content clean; there is no real malware/active-content scanner.
7. The deterministic AI safety suite currently enforces provenance integrity only; comprehensive prohibited clinical content rules are absent.
8. Cross-case/cross-facility checks were not exhaustively executed for every evidence, draft, referral, and audit resource.
9. Database-level audit immutability is absent; direct UPDATE and DELETE were accepted in rollback-only drills.
10. Full audit reconstruction from authentication through acknowledgement is impossible because later workflow stages are unavailable.
11. Provider failure, timeout, rate-limit, retry, and live duplicate-delivery matrices are incomplete.
12. Diarization, broad OCR, multilingual, noisy/silent audio, and code-switching fixtures are incomplete or not verified.
13. The latest readiness rerun hung during external Blob initialization; startup lacks demonstrated bounded timeout/recovery for that condition.
14. Metrics and distributed tracing were not demonstrated.
15. Performance samples are small, sequential, and not suitable for capacity or SLA claims.
16. Applied migration files are intentionally left outside the active formatting pass.

## 14. Final Verification Summary

### Test counts

- Primary isolated pytest collection: 195 outcomes — 192 passed, 3 skipped, 0 failed.
- The three external/live tests skipped by the isolated suite were subsequently executed with opt-in flags and passed.
- Live integration command: 4 passed; this includes two tests also present in the isolated run.
- Live E2E command: 1 passed, but it is a deliberately partial case/outbox/audit scenario.
- Coverage: 71.92% across the measured package.

### Failed or non-passing verification

- Whole-repository format check: FAIL on five historical applied migration files.
- Diarization: NOT VERIFIED with the single-speaker fixture.
- Audit database UPDATE prevention: FAIL.
- Audit database DELETE prevention: FAIL.
- Latest runtime readiness rerun: did not complete; operator-terminated after approximately 150 seconds.
- Complete golden E2E, human review/handoff, business Celery workflow, outbox recovery, and audit reconstruction: NOT VERIFIED or FAIL as classified above.

No skipped or unexecuted item is counted as a pass.

## 15. Release Decision

**RELEASE BLOCKED**

The repository is materially safer and more truthful than its starting state: authentication/consent/facility checks were hardened, schema drift was removed, real infrastructure and provider probes succeeded in several areas, fake HTTP/worker success was eliminated, logging was sanitized, production provider fallback now fails closed, and the primary suite passes.

Release remains blocked because the required authoritative workflow is not operational: async business tasks and outbox recovery are incomplete; reviewer approval, escalation, referral, and acknowledgement are not exposed as executable application paths; the full synthetic golden path and audit reconstruction cannot run; database-level audit mutation is allowed; the safety policy is incomplete; and repeatable readiness under an external Blob delay was not demonstrated.

This evidence does not support a “production ready” claim.
