# CareIntel R8 Release Evidence

## 1. Release scope

This document records the R8 final-release validation executed on 2026-09-30.
It reports observed results rather than planned behavior.

- Docker, Kubernetes, microservices, LangGraph, additional databases, vector
  stores, and brokers were excluded.
- The existing FastAPI, PostgreSQL/pgvector, Azure Blob, Redis/Celery,
  transactional outbox, Azure AI, JWT/RBAC/consent, and audit architecture was
  preserved.
- Only synthetic data was used. No real patient data or PHI was introduced.
- External infrastructure was not reset, truncated, dropped, or otherwise
  destructively modified.
- Deterministic providers were used inside the repeatable full application
  workflow. Configured Azure providers were verified separately at their real
  integration boundaries.

The 2026-09-23 evidence snapshot reported `RELEASE BLOCKED` at commit `c3fdd50`.
R4-R7 commits subsequently implemented async execution, human review/handoff,
audit immutability, security hardening, recovery behavior, and a full synthetic
application workflow. R8 re-ran those release-critical paths; it does not
retroactively describe the older snapshot as passing.

## 2. Repository and environment snapshot

| Item | Observed value |
|---|---|
| Verification time | `2026-09-30T13:35:43+05:30` |
| Branch | `E2E` |
| Verified base commit | `bc6756789d102e95624c7567c9355d2868921c60` |
| R8 working tree | Corrective changes listed in section 13; not committed |
| Package version | `0.1.0` |
| Python | `3.12.3` |
| Alembic head | `0013` |
| Dependency lock | `UV_CACHE_DIR=/tmp/careintel-r8-uv-cache uv lock --check`: PASS; 100 packages |

Production configuration remains environment-based and uses secret-valued
settings for credentials. A source scan found no committed real password, API
key, token, connection string, or signed URL. Production-mode validation rejects
debug/SQL echo, missing required external configuration, and demo/unconfigured
LLM, embedding, TTS, STT, and OCR providers.

## 3. Forensic release-readiness scan

The repository was searched for `TODO`, `FIXME`, placeholders, stubs,
`NotImplementedError`, HTTP 501, fake success, bypasses, hardcoded credentials,
disabled security checks, and debug shortcuts.

| Classification | Finding | Release impact |
|---|---|---|
| CRITICAL | None observed after verification | None |
| HIGH | Configured diarization requested plain `json`, which cannot carry speaker annotations | Fixed in R8; contract test and real Azure smoke now pass |
| MEDIUM | Five applied historical migrations contain Ruff style issues | Non-runtime; applied migration history was not rewritten for formatting |
| LOW | Unused `CapabilityNotImplementedError` definition remains available | No route raises it; runtime OpenAPI audit found no 501 release route |
| NON-BLOCKING | Demo/fake adapters occur in development and test code | Production configuration rejects them for externally wired capabilities |

No release-required route returned `501 NOT_IMPLEMENTED`. Runtime route review
found 60 registered method/path keys, 51 OpenAPI paths, no duplicate route keys,
and no debug-only route.

## 4. Final high-value verification checks

| Check | Actual command | Result |
|---|---|---|
| 1 — security, authorization, consent, audit | `.venv/bin/python -m pytest tests/unit/test_auth.py tests/unit/test_consent.py tests/unit/test_security.py tests/unit/test_handoff_security.py tests/integration/test_recovery_r6_security.py` | PASS — 32 passed in 29.58s |
| 2 — async, outbox, Celery, idempotency | `.venv/bin/python -m pytest tests/unit/workflow/test_task_service.py tests/integration/test_recovery_r4_async.py tests/integration/test_recovery_r4_celery.py` | PASS — 6 passed in 269.58s |
| 3 — full synthetic application workflow | `.venv/bin/python -m pytest tests/integration/test_recovery_stages_1_3.py` | PASS — 1 passed in 456.46s |
| 4 — failure, readiness, observability, safety | `.venv/bin/python -m pytest tests/unit/test_config.py tests/api/test_health.py tests/unit/test_startup_safety.py tests/unit/test_correlation.py tests/unit/test_logging.py tests/unit/test_errors.py tests/unit/ai/test_policy_service.py` | PASS — 47 passed in 1.46s |
| 4b — live runtime | `.venv/bin/python scripts/verify_runtime.py` | PASS — startup, liveness, readiness, auth rejection, OpenAPI, route audit, bounded probes |
| 5 — concise regression | `.venv/bin/python -m pytest -m 'not integration'` | PASS — 221 passed, 9 deselected in 62.09s |

The same test may appear in a focused check and the concise regression command;
counts above are per command and are not presented as a unique-test total.

Additional final validation:

| Verification | Result |
|---|---|
| `.venv/bin/ruff check src tests scripts` | PASS |
| `.venv/bin/ruff format --check src tests scripts` | PASS; 320 files |
| `.venv/bin/mypy src/careintel` | PASS; 250 source files |
| `.venv/bin/python -m compileall -q src tests scripts` | PASS |
| `git diff --check` | PASS |
| Azure STT request-format contract test | PASS; 2 passed in 0.10s |

## 5. Database and persistence

| Check | Verification | Result |
|---|---|---|
| PostgreSQL/Supabase connectivity | Isolated `scripts/verify_infra.py` PostgreSQL probe | PASS; 17,724.94ms |
| Applied migration | `timeout 60s .venv/bin/alembic current` | PASS — `0013 (head)` |
| ORM/schema drift | `timeout 60s .venv/bin/alembic check` | PASS — no new upgrade operations detected |
| pgvector | Live extension metadata | PASS |
| Vector dimension | Live column metadata | PASS — `vector(1536)` |
| Vector index | Live index/operator metadata | PASS — HNSW cosine index |
| Audit immutability | Direct UPDATE and DELETE attempts in rollback-isolated live test | PASS — PostgreSQL trigger rejected both |
| Outbox/task/idempotency persistence | Live integration tests | PASS |
| Workflow/review/handoff persistence | Full synthetic live-database workflow | PASS |

Migration `0013` adds audit trace fields and query indexes and installs a
PostgreSQL trigger that rejects UPDATE or DELETE on `audit_logs`. It existed
before R8 and was verified at the live database head. R8 added no migration and
did not mutate production schema manually.

The first combined infrastructure probe's database portion hit its command
timeout. A bounded isolated retry passed, and all live database-backed final
checks subsequently passed. This transient result is retained here rather than
being converted into an initial pass.

## 6. External infrastructure and configured providers

### Infrastructure

| Dependency | Executed verification | Result |
|---|---|---|
| Azure Blob | Synthetic upload, metadata, byte-integrity download, authorized time-limited access, missing-object behavior, cleanup | PASS — 12,218.82ms |
| Redis | Real ping | PASS — 3,419.41ms |
| Celery broker | Real configured broker connection | PASS — 6,202.96ms |
| Celery worker path | Real worker execution through Redis, database state update, duplicate delivery | PASS |

The Blob object was synthetic and removed by the verification script. No signed
URL, connection string, key, object content, or credential was written into this
evidence.

### Azure AI providers

`scripts/verify_providers.py` performed real configured provider calls with
synthetic inputs. It printed only outcome and timing metadata.

| Capability | Actual verification | Result | Observed latency |
|---|---|---|---:|
| Structured LLM | Schema-constrained synthetic response | PASS | 2,601.66ms |
| Prompt-injection provider boundary | Adversarial synthetic fixture safely rejected by provider content filtering | PASS for fixture | 3,187.72ms |
| Embedding | Exactly 1,536 values | PASS | 1,669.74ms |
| TTS | Nonempty synthetic MP3 | PASS | 9,873.65ms |
| STT | Nonempty transcript from synthetic TTS audio | PASS | 3,726.29ms |
| Diarization | Provider-supplied speaker label after R8 response-format correction | PASS for single-speaker fixture | 4,531.09ms |
| Document Intelligence | Native synthetic PDF text and page provenance | PASS | 8,638.91ms |

The first post-fix diarization attempt timed out inside the restricted network;
an unbuffered retry identified a network `ConnectError` during TTS. One approved,
bounded external-network rerun then passed both TTS synthesis (4,241.85ms) and
diarization. No unavailable provider response was treated as success.

## 7. Full synthetic E2E and audit reconstruction

The full application-service test used a live configured PostgreSQL database,
synthetic identities/data, transactional service boundaries, durable outbox/task
records, and deterministic provider adapters. It did not insert final review or
handoff states directly.

Executed path:

`Auth -> Consent -> Case -> Encounter -> Evidence -> Processing -> OCR/STT-like
derived artifacts -> Extraction -> Provenance -> Timeline -> Missing Information
-> Hybrid Retrieval -> AI Draft -> Validation/Safety -> Outbox -> Durable Task
-> Reviewer Queue -> Assignment -> Workspace -> Review -> Human Approval ->
Referral/Handoff -> Send -> Recipient Acknowledgement -> Completion`

Persisted assertions included:

- active consent and authorized case/encounter ownership;
- three original evidence records preserved separately from derived processing;
- processing, extraction, timeline, missing-information, retrieval, AI run, and
  AI draft records;
- provenance on structured and AI-derived content;
- advisory AI output passing schema, identifier, evidence, provenance,
  missing-information, prohibited-content, and deterministic policy validation;
- durable outbox and async-task records with idempotent execution;
- reviewer queue, assignment, workspace source visibility, explicit human
  decision, and stale-write protection;
- cross-facility workspace denial;
- finalized referral package, send request, SENT state, recipient
  acknowledgement, and only then COMPLETED state;
- repeated acknowledgement and invalid transitions do not duplicate or bypass
  business effects;
- audit reconstruction across authentication, consent, case, encounter,
  processing, structuring, retrieval, AI, review, outbox/task, handoff, send,
  acknowledgement, and completion events;
- correlation/causation metadata on the application, dispatcher, and worker
  portions of the flow;
- original synthetic narrative absent from serialized audit metadata.

The E2E uses a mocked Celery sender so it can deterministically drive the durable
executor; Check 2 independently verifies the same business task through a real
Celery worker and Redis broker. Real Azure provider boundaries are verified in
section 6.

## 8. Security and safety evidence

| Area | Executed behavior | Result |
|---|---|---|
| JWT authentication | Missing, malformed, expired, forged, wrong issuer/audience/signature | PASS |
| Authorization/RBAC | Permission, role, case/facility, review, handoff, and acknowledgement denial paths | PASS for release-critical paths |
| Consent | Missing, withdrawn, invalid/stale/mismatched consent and protected processing | PASS |
| Reviewer/handoff authorization | Unrelated actor cannot review or acknowledge; permitted sender/recipient manager can | PASS |
| Audit | Append-only repository and database trigger; trace metadata sanitized | PASS |
| Idempotency/replay | Duplicate API/task/outbox/handoff effects remain single | PASS |
| Optimistic concurrency | Stale reviewer/workflow version raises deterministic conflict | PASS |
| Workflow protection | Mandatory approval, no acknowledgement before send, SENT not COMPLETED, completion requires acknowledgement | PASS |
| AI schema/provenance/policy | Unsupported identifiers, claims, citations, provenance, missing information, and prohibited output rejected | PASS |
| Prompt injection | Patient, OCR, STT, extracted fields, and retrieved text remain untrusted data; no arbitrary tool/workflow authority | PASS for executed matrix |
| Cross-case isolation | Retrieval/context/workspace authorization does not mix case/facility data | PASS for executed paths |
| Sensitive logging | Executed output and structured-log tests contain no secret or raw narrative leakage | PASS for executed paths |

CareIntel continues to treat AI output as reviewer-facing advisory content. The
AI path cannot approve, escalate, refer, acknowledge, complete, or otherwise
mutate authoritative workflow state.

## 9. Failure, recovery, health, and observability

| Scenario | Result |
|---|---|
| Transient outbox/task failure, retry, success | PASS |
| Duplicate delivery | PASS — no duplicate business side effect |
| Retry exhaustion/permanent failure | PASS — explicit sanitized FAILED state |
| Stale task recovery | PASS |
| Stale reviewer update | PASS — conflict, no overwrite |
| Referral send failure | PASS — explicit recoverable state |
| Missing acknowledgement | PASS — remains SENT, not COMPLETED |
| Provider failure/malformed output/policy rejection | PASS — explicit failure; no fabricated fallback or approval |
| Missing Blob object | PASS — explicit failure |
| Unavailable dependency | PASS for bounded readiness behavior; readiness reports failure rather than hanging |

R8 changed the per-dependency readiness timeout default from 5 seconds to the
existing bounded maximum of 30 seconds. The configured Supabase path exceeded
the old 5-second bound during one live run; after correction, readiness returned
success in 13,346.89ms with PostgreSQL, Redis, and Blob all healthy. Liveness did
not depend on external probes.

Trace identifiers are propagated through request context, services, audit,
outbox, dispatcher, worker/task, review, and handoff records. Health-route access
logs are suppressed by route template rather than hardcoded mount prefix, which
removed 100 redundant liveness log entries without suppressing failures.

Runtime verification observed:

| Measurement | Observed value |
|---|---:|
| In-process liveness mean | 0.408ms |
| p50 | 0.382ms |
| p95 | 0.526ms |
| p99 | 0.680ms |
| Live readiness | 13,346.89ms |
| Full synthetic workflow | 456.46s |

These are raw small-sample observations, not capacity results or SLAs. The E2E
duration includes remote database latency and intentionally broad workflow
coverage.

## 10. Release gates

### G0 — Environment / Configuration

- **STATUS:** PASS
- **EVIDENCE:** Lock check, active-source lint/format/type/compile, production
  fail-closed configuration, source secret scan, application startup, and route
  audit passed.
- **FAILURE:** Historical applied migrations retain style-only Ruff findings.
- **IMPACT:** No runtime or schema impact.
- **REMAINING ACTION:** Keep applied migration history immutable; enforce style
  for new migrations.

### G1 — Database / Persistence

- **STATUS:** PASS
- **EVIDENCE:** Live `0013` head, no Alembic drift, pgvector extension,
  `vector(1536)`, HNSW cosine index, audit trigger, outbox/idempotency, and full
  workflow persistence verified.
- **FAILURE:** Initial combined database probe timed out; bounded isolated retry
  and all subsequent database-backed checks passed.
- **IMPACT:** No repeatable persistence failure observed.
- **REMAINING ACTION:** Continue monitoring managed-database latency.

### G2 — Storage / External Infrastructure

- **STATUS:** PASS
- **EVIDENCE:** Real Azure Blob upload/download/integrity/access/missing/cleanup,
  Redis ping, broker connectivity, Celery execution, and configured Azure
  LLM/embedding/TTS/STT/diarization/OCR probes passed.
- **FAILURE:** None release-critical in executed scope.
- **IMPACT:** None observed.
- **REMAINING ACTION:** Expand non-release fixture breadth listed in section 12.

### G3 — Authentication / Security

- **STATUS:** PASS
- **EVIDENCE:** 32-test focused security gate plus cross-facility workspace
  denial, consent enforcement, database audit immutability, replay protection,
  stale-write conflict, and log-safety checks passed.
- **FAILURE:** No release-critical failure observed.
- **IMPACT:** None observed.
- **REMAINING ACTION:** Continue adversarial expansion as providers and routes
  evolve.

### G4 — Core Application Workflow

- **STATUS:** PASS
- **EVIDENCE:** Full live-database application workflow persisted processing,
  structuring, timeline, missing information, hybrid retrieval, AI validation,
  provenance, review, and audit state.
- **FAILURE:** No release-critical failure observed.
- **IMPACT:** None observed.
- **REMAINING ACTION:** None for the verified release path.

### G5 — Async Workflow / Execution

- **STATUS:** PASS
- **EVIDENCE:** Transactional outbox creation/claim/dispatch/replay, real
  Redis/Celery worker execution, database task state, retry bounds, stale
  recovery, causation, and duplicate-delivery idempotency passed.
- **FAILURE:** No release-critical failure observed.
- **IMPACT:** None observed.
- **REMAINING ACTION:** No disruptive shared-Redis outage drill was performed.

### G6 — Human Review / Handoff

- **STATUS:** PASS
- **EVIDENCE:** Queue, assignment, workspace evidence/provenance visibility,
  draft acceptance, explicit human decision, authorization, optimistic locking,
  referral package, send, acknowledgement, completion, and audit passed.
- **FAILURE:** No release-critical failure observed.
- **IMPACT:** None observed.
- **REMAINING ACTION:** None for the verified release path.

### G7 — Full E2E / Release Evidence

- **STATUS:** PASS
- **EVIDENCE:** The deterministic full workflow, independent real async path,
  configured external integrations, readiness/route checks, audit
  reconstruction, static validation, and concise regression check passed.
- **FAILURE:** No release-critical failure observed.
- **IMPACT:** None observed.
- **REMAINING ACTION:** Treat the scope limitations below as follow-up
  verification, not as hidden passes.

## 11. API, performance, and resource-safety review

- Runtime OpenAPI generation passed with 51 paths and no duplicate/debug route.
- Missing and malformed JWTs were rejected at the live application boundary.
- Liveness is local; readiness reports PostgreSQL, Redis, and Blob dependency
  health with bounded probes.
- Critical queue, audit, review, handoff, status, idempotency, knowledge-filter,
  and vector-retrieval paths have intentional indexes through migration `0013`.
- Async payloads use identifiers and safe metadata rather than raw documents,
  transcripts, credentials, or tokens.
- Provider calls use explicit timeouts; retries are bounded and distinguish
  retryable from permanent failures.
- No demonstrated release-path N+1 query, unbounded result load, repeated AI or
  embedding call, or fake 202/task-completion path remained.
- Blob objects remain private and original evidence is distinct from derived
  artifacts.

No load test or capacity benchmark was executed. This evidence makes no
throughput, concurrency, availability, or clinical SLA claim.

## 12. Known limitations and not-verified items

1. Multi-speaker separation was not measured; the executed diarization fixture
   contains one synthetic speaker, though the configured adapter returned an
   actual speaker label.
2. OCR was executed against a native PDF with page provenance. Scanned,
   table-bearing, poor-quality, and unreadable document fixtures were not rerun
   during R8.
3. Noisy, silent, multilingual, and code-switched audio matrices were not run.
4. The full E2E uses deterministic provider adapters for repeatability; real
   Azure providers were verified separately rather than invoked repeatedly from
   the 456-second workflow.
5. The E2E seeds initial synthetic evidence/input records, then uses actual
   application services for processing through completion. Intake validation
   and real Blob storage are covered by separate tests/probes.
6. Destructive database, Redis interruption, worker-process crash, and shared
   external-service outage drills were not performed against managed resources.
7. No statistically meaningful load, concurrency, capacity, or endurance test
   was performed.
8. Log-safety verification covers structured-log tests and executed outputs; it
   is not a formal privacy/compliance certification or exhaustive production
   sink audit.
9. Historical migration formatting issues remain intentionally untouched.

None of these items produced a failure in the release-critical verified path.
They must not be represented as independently verified capabilities.

## 13. R8 corrective changes

R8 made only evidence-backed corrections discovered during validation:

- increased the bounded readiness probe default from 5 to 30 seconds because
  the real managed database exceeded 5 seconds;
- made health-route log suppression independent of the router mount prefix;
- changed Azure diarization requests from `json` to `diarized_json` while
  preserving standard STT `json` responses;
- added request-format regression coverage;
- strengthened the full synthetic workflow's reviewer-workspace, source
  visibility, cross-facility authorization, trace-context, and audit
  reconstruction assertions;
- reformatted one pre-existing test statement.

No migration was added or changed during R8.

## 14. Release decision

**RELEASE READY**

All release-critical G0-G7 gates passed using executed evidence. The current
repository demonstrates the authoritative PostgreSQL workflow from synthetic
authentication and consent through processing, retrieval, bounded AI,
deterministic validation, real outbox/Celery execution, human approval,
referral, recipient acknowledgement, completion, and audit reconstruction.

This decision is limited to the verified configuration and workflows recorded
above. It is not a certification, does not eliminate the known limitations, and
does not turn unexecuted fixture matrices or capacity claims into passes.
