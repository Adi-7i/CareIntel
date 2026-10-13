# CareIntel — Backend–Frontend Gap Analysis and Requirements

Quick links: [API inventory](#audit-section-6) · [Frontend inventory](#audit-section-7) · [Gap matrix](#audit-section-9) · [Requirements](#audit-section-15) · [Backend blockers](#audit-section-17) · [Readiness](#audit-section-20) · [Evidence/limits](#audit-section-21)

<a id="audit-section-1"></a>

## 1. Document purpose and status

**Audit date:** 9 October 2026. **Repository snapshot:** `1d96313` (current checkout inspected). **Deliverable:** `frontend/requirement.md`. No frontend documentation directory or existing file with this name was found. **Status:** repository-grounded working specification, pending product, clinical, security and architecture decisions; no implementation or integration authorized by this document.

This specifies frontend work before the user’s Phase 10 backend integration. It distinguishes working source behavior, incomplete contracts, documented requirements and optional proposals. The PRD itself is a draft, not an approved clinical protocol. Synthetic or permitted public sample data only; no live-patient use, autonomous diagnosis, prescribing, AI-controlled final priority or deployment/compliance claims.

Identifiers: `B-xxx` = audited backend capability; `F-xxx` = frontend foundation capability; `FE-xxx` = frontend requirement; `BG-xxx` = backend dependency/gap; `DEC-xxx` = unresolved decision; `E-xx` = inspected evidence group. References to API schemas and services resolve through sections 6 and 21. Proposed routes are explicitly proposals.

**Verification semantics:** `Implemented and verified` means the operation was traced in inspected source through its relevant layers, with test-source corroboration where available. It does **not** mean an API, provider, database migration or test was executed in this audit. Partial behavior is marked `Partially implemented`; absence of an operational contract remains a gap even when a table or service exists. Historical test results are attributed only to `RELEASE_EVIDENCE.md`.

<a id="audit-section-2"></a>

## 2. Executive summary

The backend is a substantive FastAPI modular monolith, with PostgreSQL/pgvector persistence, JWT sessions, permission and facility checks, purpose-specific consent, multimodal processing, retrieval, advisory drafts, durable workers, human review, escalation and simulated handoff. All **14 registered router modules**, **52 application HTTP method/path pairs**, **52 ORM table declarations** and **15 migration revisions** were inventoried. These numbers describe source declarations, not applied infrastructure.

The frontend contains **13 page routes** across nine functional areas: authentication/root entry, dashboard, cases, evidence, intelligence, review, escalation, handoff and design-system examples. Its workflow forms validate local inputs and end in disconnected messages. No actual API integration, authenticated session, permission-aware navigation or connected case workflow was found. `/` correctly redirects to `/login`; that entry behavior must remain.

The most consequential findings are:

- Patient identity is a `synthetic_subject_id` UUID, not a patient profile. There is no patient-name/demographic intake schema or lookup API. Consent subjects reference `users.id`; the service-level tests provision subject users outside public intake. A staff user’s `display_name` is not evidence of a patient-name feature.
- Case creation requires an active matching `data_processing` consent at notice version `1.0`. The current case form instead collects title, MRN/distinct identifier, mandatory routine/urgent/stat priority and a checkbox. Those fields do not match the contract and imply an unsupported clinical priority workflow.
- File upload accepts one file per request associated with an existing case, with optional encounter. Multiple files can be represented as separate evidence records. `NoOpScanner` is the actual composition choice and always returns `PENDING`; files stay `STORED`, while processing and download require `READY`. A scanner port is not a working scan lifecycle.
- Text intake writes modality `"TEXT"`, while `EvidenceModality` and the response schema expect `"text"`. This is a source-level response-validation inconsistency; the language-processing branch also compares lowercase modality. Do not claim public text intake works end to end until corrected and tested.
- Async trigger returns an **AsyncTask ID** under the name `run_id`. Task read responses omit their stored result; processing responses omit the `ExtractionRun.id` required by structuring. A browser cannot safely reconstruct the processing chain from existing public contracts.
- Review edit immediately marks a draft `APPROVED`; the workspace still returns original AI content, while referral uses the latest human edit. No edit-history API, material-change/reapproval workflow, field-correction API or usable manual note path exists. AI validation/policy failures persist reviewer status `REJECTED`; the DRAFT-only review guard blocks accept/edit of those outputs. The generic case-transition API can reach review/referral/completion states without the specialized approval/acknowledgement invariants.
- Manual escalation exists only from an active review queue and requires AI-analysis consent. It does not satisfy the documented intake/AI-outage bypass. Clarification has an unregistered, incomplete service and generated questions, but no answer/stop/return workflow.
- Handoff send enqueues delivery; it is distinct from `SENT`, acknowledgement and completion. Simulated non-production delivery is supported; live delivery, separate receipt/rejection/acceptance, acknowledgement timeout ownership and a durable handoff read contract are missing.
- **RBAC does not by itself provide a staff-management interface or staff-creation workflow.** There is a one-time first-admin CLI and generic user/role records, but no staff provisioning, invitations, activation/deactivation, directory, facility entity or facility configuration API. Migration `0015` gives admin every permission, including clinical ones; this conflicts with the problem document’s separation of technical administration from clinical authority and STARTUP’s older description.

The capability and gap counts are derived from section 9’s rows, not endpoints or pages. Backend-only controls and blocked product requirements are kept separate from frontend implementation work. Section 16 orders delivery around access boundaries, intake/evidence, reviewer integrity and acknowledged handoff.

<a id="audit-section-3"></a>

## 3. Scope and audit methodology

Discovery used actual file listings and `rg`, then registered router composition, schemas, dependencies, service methods, domain states, ORM/repositories, migration seeds, provider wiring, worker handlers and test source. All frontend pages and their imported user-facing feature components were inspected, including submit handlers, local validation and navigation. Provider implementation was distinguished from configuration selectors and deterministic demo adapters. No secrets, environment values, report content or patient records were copied.

### Audit coverage checklist

| Area | Coverage and result |
|---|---|
| Repository/application composition | Complete for current checkout: entry point, router aggregate, dependency wiring, frontend root/layout/package conventions |
| Registered APIs | All 14 router modules and 52 method/path pairs; section 6 retains every route |
| Authentication/RBAC/consent | Services, policy, sessions, user mappings, migrations `0002`–`0015`, bootstrap and relevant tests traced |
| Case/encounter/intake | Schemas, commands, services, state/history/outbox/repositories, synthetic subject relationship and frontend forms traced |
| Evidence/storage/scanning | Multipart/text routes, checksums/MIME/size, storage, scanner, state guards, download, consent/encounter checks and tests traced |
| Processing/language/extraction | Four processor types, provenance/source-run dependencies, provider wiring, persisted output, failures and frontend controls traced |
| Structuring/retrieval/AI | Timeline/conflict/missing/question generation; knowledge publication; search/pinning; context/validation/policies/drafts traced |
| Review/escalation/handoff | Queue access/eligibility/versions; edit/decision/package/send/ack/complete; unregistered clarification inspected |
| Workers/events/recovery | Six dispatcher mappings, executor, Celery tasks, actor hydration, retry/stale recovery and operational scripts inspected |
| Persistence/migrations/security | All 52 ORM declarations and 15 revisions inventoried; relevant FKs, scope, uniqueness, audit trigger and indexes inspected |
| Tests | All 57 test-bearing modules inventoried by source; principal unit/API/integration/security/E2E implementations inspected. None run; no new fixtures generated |
| Frontend | All 13 pages, seven shell navigation items, auth/case/evidence/intelligence/review/escalation/handoff components and 17 shared UI files inventoried |
| Product sources | Available 18-page PRD and 52-page problem-understanding PDFs read; repository docs reconciled. DRES and original PS03 PDF unavailable |
| Boundaries | No API calls, runtime startup, database reads/writes, provider calls, package installs, tests, migrations or application edits |

Coverage is systematic source inspection, not an independent clinical validation, penetration test, load test or browser accessibility certification. Negative findings concern the inspected checkout; undocumented external systems cannot be assumed.

<a id="audit-section-4"></a>

## 4. Repositories and source documents inspected

| Artifact | Actual location/version | Authority and limitation |
|---|---|---|
| Current repository/backend | `/home/lucifer/Desktop/CareIntel`; `src/careintel`; `pyproject.toml`, `uv.lock` | Primary implementation evidence; other CareIntel directories are separate copies and not part of this checkout |
| Frontend | `frontend/src/app`, `frontend/src/components`, `frontend/package.json`, `frontend/AGENTS.md` | Next.js App Router, React/TypeScript, Tailwind v4, shadcn/Base UI wrappers, Lucide; pnpm package manager |
| PRD [P] | `/home/lucifer/Downloads/CareIntel_Product_Requirements_Document_v1.pdf`; internal version **0.1**, 14 September 2026, 18 pages | Draft product requirements, `FR-001`–`FR-033`, `SEC-001`–`SEC-009`, `NFR-001`–`NFR-010`, decisions `D01`–`D12`; filename “v1” does not change internal version |
| Problem understanding [U] | `/home/lucifer/Downloads/CareIntel_Master_Problem_Understanding.pdf`; version **1.0**, 14 September 2026, 52 pages | Research/design baseline; references original PS03; assumptions and open questions are not approval |
| DRES | Not found in repository or searched project/document/download locations under `/home/lucifer` | Code comments refer to it; original sections/IDs cannot be verified. Obtain exact authoritative artifact before asserting conformance |
| Original PS03 | `Problem_Statement_3.pdf` referenced by [U], unavailable in searched files | Requirements visible through PRD/problem baseline only; original acceptance/weighting text cannot be independently reconciled |
| Repository docs | `README.md`, `STARTUP.md`, `RELEASE_EVIDENCE.md` | Context and historical evidence; contradictions below prevent treating prose as current implementation proof |
| Frontend docs | `frontend/README.md`, `frontend/AGENTS.md`, component notes | README is scaffold text, mentions Geist and alternative package managers; actual CSS uses Times New Roman and task requires pnpm only |
| External setup plan | `/home/lucifer/Documents/implementation_plan.md` | Pending infrastructure plan, not authoritative backend specification; source inventory supersedes its table/permission counts |

### Reconciliation of conflicting statements

| Conflict | Concrete sources | Implementation impact / unresolved decision |
|---|---|---|
| README says review/handoff return 501 and workers fail as scaffolds; R8 says persisted workflow | README “Capability matrix”/“Current implementation boundary”; RELEASE_EVIDENCE §§4,7,14; current routers/services/workers [E-01, E-14–E-18] | Current source has operational service-backed handlers, not those old stubs. Do not request frontend pages on an assumed 501 contract. Historical release readiness is limited to its configuration/seeded service path |
| Audit mutation protection absent in README, present in source | README capability matrix; migration `0013`, AuditRepository, R6 test [E-19] | Source implements UPDATE/DELETE rejection trigger; applied state not queried here. No audit read UI/API follows from that trigger |
| Technical admin has no clinical authority versus current seed grants | [U] “Actors and accountability”, p9; STARTUP §13; migration `0014` then additive `0015` [E-03] | `0015` maps all 26 permissions to admin. Confirm authoritative clinical separation and change backend before treating admin as qualified reviewer (DEC-02) |
| Qualified reviewer requirement versus permission-only eligibility | [P] FR-019/023/029; [U] role/competence discussion; `ReviewService._eligible_reviewer`, migrations [E-14] | Nurse/health_worker receive `review:write`; eligibility is active user + permission + scope, not qualification. Approver eligibility requires DEC-02 |
| Explicit approval/new draft after material edits versus edit-as-approval | [P] FR-019–021; `DraftReviewService.edit_draft`, `WorkspaceService`, referral service [E-15] | Save/edit cannot safely be represented as neutral editing. Reapproval/content/version contracts require BG-010 before FE-020/021 |
| Manual escalation at intake/AI outage versus review-only gate | [P] FR-024/NFR-001; [U] manual bypass discussion p13; EscalationService/ReviewAccessGuard [E-16] | No UI-only workaround; BG-012 and DEC-05 must establish authorized early escalation |
| Optional malware scan versus security Must | [P] FR-011 “Should” versus SEC-003 “Must”, safety/privacy sections | Secure release policy unresolved (DEC-07); actual NoOpScanner blocks files. Never bypass readiness to satisfy a demo |
| English/Hindi target versus demo normalization | [P] scope/language quality gates; main/worker wiring [E-10] | Providers/configuration flags do not prove translation quality. Restrict claimed support to validated permitted samples (DEC-06) |
| “Release ready” versus public intake gaps | RELEASE_EVIDENCE §§7,12,14; tests seed READY evidence; scanner/text modality source [E-06,E-20] | Historical service/provider tests do not prove browser→upload→scan→processing. Phase 10 requires public-contract tests after backend fixes |
| Naming/format defaults versus approved release scope | [P] D05/FR-006, source defaults [E-06] | Allowlist is upload policy, not proof every extension works with chosen OCR/STT provider. Approve supported combinations before frontend claims |

<a id="audit-section-5"></a>

## 5. Backend architecture and module inventory

`main.create_app` composes middleware, global error handlers and `/api/v1`. Request dependencies build application services with async SQLAlchemy repositories. Domain modules define commands, states, consent and authorization policies. PostgreSQL is authoritative; search uses PostgreSQL FTS and pgvector, not a separate vector database. Azure Blob and provider ports are external; Redis/Celery and database outboxes execute background tasks.

| Module / evidence | Implemented layers and meaningful operations | Important limit |
|---|---|---|
| Core/health [E-01,E-21] | Settings/startup safety, correlation/request/causation IDs, JSON errors/logging, transaction lifecycle, liveness and bounded DB/Redis/blob readiness | No operational metrics/exporter/alert dashboard contract; applied infrastructure unverified |
| Authentication/authorization [E-02,E-03] | bcrypt, JWT issuer/audience/expiry/session IDs, DB session revocation, current DB user permissions/scope, first-admin CLI | No refresh, recovery, staff lifecycle or facility directory; scope/permission association and clinical separation gaps |
| Consent [E-04] | REQUESTED→ACTIVE→WITHDRAWN, exact subject/purpose/version checks, events/audit | No read/list, disclosure/data-class record, reconsent workflow or scoped management authorization |
| Cases/encounters [E-05] | UUID synthetic subject, nullable facility, versioned state/history/outbox, create/read encounters | No patient name, search/list, ownership change, intake correction or reopen; generic transition bypasses specialized invariants |
| Evidence/storage/scanner [E-06,E-07] | Original text/file records, encounter membership, post-review write guard, checksum duplicates, size/MIME/extension checks, blob/SAS, lifecycle histories | TEXT/lowercase mismatch; scanner pending; public listing/raw text/delete missing; blob/DB atomic recovery unverified |
| OCR/STT [E-08,E-09] | Temp-file processing, persisted pages/regions/tables and transcript intervals/speakers; Azure adapters and deterministic demos | Public output reads incomplete; OCR confidences often null, STT can fabricate fallback interval; no correction contract |
| Language/extraction [E-10] | LanguageResult and original/normalized candidate values/provenance, validates exact source run and evidence intervals/spans | Always demo-wired; only fever/first ISO date extracted; no patient/report field completeness, correction/undo or calibrated confidence |
| Structuring [E-11] | Persisted run, conservative temporal normalization, conflict candidate links, checklist/missing states and bounded first-round templates | Single extraction input, onset-only conflicts, no encounter anchor, answer/stop/resolution API; demo checklist |
| Knowledge/retrieval [E-12] | Internal source/version/chunk/embed/publish/retire; published/version-filtered dense+sparse search and RRF; immutable run/candidate provenance | No knowledge-management/source-read/corpus-discovery routes; no governed clinical corpus verified; top_k absent from dedup identity |
| Advisory AI [E-13] | SafeContext, four task types, schema/reference/provenance checks, deterministic policy, run/draft/policy persistence, sanitized failure | No auto disposition; metadata/read/fallback gaps; no current provider evaluation or calibrated reliability claim |
| Review/clarification [E-14,E-15] | Queue, assignment/reassignment/start, assigned-reader workspace, accept/reject/edit, explicit decision and version locks | Queue pagination not exposed; permission-only eligibility, edit auto-approval, raw/edited mismatch, no version/read/correction/manual note/return contracts; clarification unregistered |
| Escalation [E-16] | OPEN/RESOLVED records, reasons/actor, case+queue transitions and versions | Requires active review/AI consent; ACKNOWLEDGED enum without action, no independent ownership/timeout/read API |
| Referral/handoff/recipient [E-17] | Current human-approved package, selected evidence, package supersession/finalize, recipient list, send outbox, demo worker, ack/complete | No preview/detail read, fresh approval check at finalize/send, facility recipient scope, receipt/rejection/acceptance/followup/live channel |
| Tasks/outbox/workers [E-18] | Durable task states/results, SQL claims, bounded retries, idempotency, actor rehydration, stale recovery, six business-task handlers | Result omitted from API; worker rejects FAILED processing results; failed work transaction/result discovery limits; unsupported notification events fail; no websocket/SSE/retry UI contract |
| Audit/privacy/retention [E-19] | Append, trace metadata, key redaction, DB mutation trigger; request errors avoid raw inputs | No read/export audit or comprehensive lifecycle deletion; redaction is keyed, not free-text PHI detection; platform encryption/backups not verified |
| TTS [E-22] | Authenticated text-to-binary audio, length/nonempty checks, demo/Azure port and processing audit | No purpose/case/role permission gate beyond authenticated active user; optional UX, not patient voice intake |

### Persistence coverage

The 52 ORM tables are: identity/session **6** (`users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `token_sessions`); consent **2**; case **4**; evidence **4**; processing **9**; structuring **7**; knowledge **5**; retrieval **2**; AI **3**; review/escalation **5**; referral/handoff/recipient **3**; task **1**; audit **1**. Actual declarations reside in `src/careintel/persistence/models/{user,session,consent,case,evidence,processing,structuring,knowledge,retrieval,ai,review,handoff,workflow,audit}.py`.

Migrations: `0001_foundation`, `0002_auth_security`, `0003_case_management`, `0004_evidence`, `0005_processing`, `0006_structuring`, `0007_retrieval_ai`, `0008_async_workflow`, `0009_human_review_and_handoff`, `0010_embedding_dimension_azure`, `0011_recovery_processing_source`, `0012_async_review_recovery`, `0013_audit_immutability_observability`, `0014_admin_permission_contract`, `0015_seed_role_permissions`. Source head is `0015`; the R8 report’s applied head `0013` is historical, not a current schema check.

### State and event contracts

- **Case:** CREATED→CONSENTED→INPUT_RECEIVED→PROCESSING→EXTRACTING→NORMALIZING→RETRIEVING→AI_ANALYSIS→SAFETY_CHECK→TRIAGE_DRAFT_READY→REVIEW_PENDING; review branch to REVIEWED or ESCALATED; ESCALATED→REVIEW_PENDING; REVIEWED→REFERRED/COMPLETED; REFERRED→COMPLETED. Any nonterminal may become FAILED. No general reopen. These are technical workflow states, not clinical priority labels.
- **Evidence:** PENDING_UPLOAD→STORED; scanner CLEAN→READY, REJECTED→QUARANTINED. DELETE_PENDING/DELETED/DELETE_FAILED/FAILED exist in the state model; no public deletion workflow. Text is intended READY. READY means available for processing/download, not clinically verified.
- **Queue:** PENDING_ASSIGNMENT, ASSIGNED, IN_REVIEW, CLARIFICATION_PENDING, REVIEW_COMPLETE, ESCALATED. The clarification enum has no registered command. Queue `priority_bucket` is persisted but no approved urgency policy/UI assignment contract was found.
- **Draft:** AI run IN_PROGRESS/COMPLETED/FAILED/REJECTED/POLICY_BLOCKED; validation ACCEPTED/REJECTED/REPAIR_ATTEMPTED; human DRAFT/APPROVED/REJECTED. These axes must remain distinct.
- **Handoff:** DRAFT→READY→SENDING→SENT→ACKNOWLEDGED→COMPLETED; DELIVERY_FAILED can retry; ACKNOWLEDGEMENT_PENDING/CANCELLED have domain transitions without dedicated HTTP commands. No separate received/accepted/rejected contract.
- **Task:** PENDING, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED; no cancel endpoint. Technical retry/backoff values are not clinical followup thresholds.
- **Dispatchable events:** EVIDENCE_PROCESSING_REQUESTED, RETRIEVAL_REQUESTED, AI_RUN_REQUESTED, CASE_WORKFLOW_ADVANCE, STRUCTURING_REQUESTED, HANDOFF_SEND_REQUESTED. Case-created, evidence-uploaded/text-registered and completion notifications do not automatically run the entire pipeline; dispatcher marks unsupported types failed. Event production alone does not establish an orchestrated user workflow.

<a id="audit-section-6"></a>

## 6. Backend API and workflow inventory

All paths below include the verified mount `/api/v1`. All business routes use authenticated JWT sessions unless stated. Listed permissions are actual service/dependency checks; facility scope and active user are additional guards. `DP`, `AI`, `RF` mean active consent for `data_processing`, `ai_analysis`, `referral` respectively, exact notice `1.0`. Consent `export` exists as an enum only. Error behavior uses the envelope below unless an unresolved failure falls through to 500.

### Complete registered HTTP inventory

| API ID | Method/path | Request → response | Actual permission / consent | Behavior and readiness limit |
|---|---|---|---|---|
| A01 | POST `/api/v1/auth/login` | LoginRequest → TokenResponse | Public credentials | Email/password; persisted JWT session; no refresh token |
| A02 | POST `/api/v1/auth/logout` | Bearer header → 204 | Valid token/session processing | Revokes current session, not every session |
| A03 | GET `/api/v1/auth/me` | — → UserProfileResponse | Current active user | id, active, roles, permissions; facility scopes/name/email omitted |
| A04 | POST `/api/v1/consent/request` | ConsentRequest → ConsentResponse, 201 | consent:write | subject/purpose/notice strings; initial actor null; subject FK user |
| A05 | POST `/api/v1/consent/{consent_id}/capture` | — → ConsentResponse | consent:write | REQUESTED→ACTIVE; no subject/facility management check |
| A06 | DELETE `/api/v1/consent/{consent_id}` | — → ConsentResponse | consent:write | ACTIVE→WITHDRAWN; no read API or cascade deletion |
| A07 | POST `/api/v1/cases` | CreateCaseRequest → CaseResponse, 201 | case:write / DP | synthetic_subject_id, optional facility_id, consent_id; state CREATED |
| A08 | GET `/api/v1/cases/{case_id}` | UUID → CaseResponse | case:read | Facility-denied discovery masked 404 |
| A09 | POST `/api/v1/cases/{case_id}/transitions` | TransitionRequest → CaseResponse | case:write | to_state, expected_version, optional reason; enum transition only, no review/ack invariant |
| A10 | GET `/api/v1/cases/{case_id}/history` | UUID → CaseHistoryResponse | case:read | State history, not general audit or note versions |
| A11 | POST `/api/v1/cases/{case_id}/encounters` | CreateEncounterRequest → EncounterResponse, 201 | case:write / DP | encounter_type 1–100, occurred_at datetime, optional notes ≤2000 |
| A12 | GET `/api/v1/cases/{case_id}/encounters` | UUID → EncounterListResponse | case:read | Case-scoped encounter records; no patient profile |
| A13 | POST `/api/v1/evidence/text` | RegisterTextRequest → EvidenceResponse, 201 | evidence:write / supplied DP | case_id, text_content ≤20000, consent_id, optional encounter_id/source_language; modality mismatch BG-005 |
| A14 | POST `/api/v1/evidence/files` | Multipart → EvidenceResponse, 201 | evidence:write / supplied DP | case_id, consent_id, modality, one file, optional encounter_id; STORED pending scanner |
| A15 | GET `/api/v1/evidence/{evidence_id}` | UUID → EvidenceResponse | evidence:read | Metadata only; no raw text body |
| A16 | GET `/api/v1/evidence/{evidence_id}/download` | UUID → SecureDownloadResponse | evidence:read | READY + storage key; short-lived read SAS; no current consent recheck |
| A17 | POST `/api/v1/processing/execute` | TriggerProcessingRequest → ProcessingRunResponse | processing:write / DP | Runs one step synchronously; response can be FAILED; not provider progress |
| A18 | POST `/api/v1/processing/trigger` | TriggerProcessingRequest → TriggerProcessingResponse, 202 | processing:write / DP | Returns task ID as run_id; outbox dispatch required |
| A19 | GET `/api/v1/processing/runs/{run_id}` | ProcessingRun UUID → ProcessingRunResponse | processing:read / DP | Status/provider/config/times/failure only; no derived-result payload |
| A20 | POST `/api/v1/cases/{case_id}/evaluate` | EvaluateRequest → EvaluateResponse | structuring:write / DP | ExtractionRun UUID, not ProcessingRun UUID; counts/run metadata |
| A21 | GET `/api/v1/cases/{case_id}/timeline` | — → TimelineEventResponse[] | structuring:read / DP | Latest successful run, date/unresolved/source/candidate/extraction fields |
| A22 | GET `/api/v1/cases/{case_id}/conflicts` | — → ConflictResponse[] | structuring:read / DP | Candidate/value links omitted |
| A23 | GET `/api/v1/cases/{case_id}/missing-info` | — → MissingInfoResponse[] | structuring:read / DP | Checklist status/materiality/resolution |
| A24 | GET `/api/v1/cases/{case_id}/questions` | — → QuestionResponse[] | structuring:read / DP | Read-only generated question/round/status; no answer/stop |
| A25 | GET `/api/v1/cases/{case_id}/summary` | — → StructuringSummaryResponse | structuring:read / DP | Latest run ID/extraction ID/counts; 404 without successful run |
| A26 | POST `/api/v1/cases/{case_id}/retrieval` | RetrievalRequest → RetrievalResponse | knowledge:read / AI | Query 1–4000, corpus_version 1–100, HYBRID/DENSE/SPARSE, top_k 1–50 (default 10) |
| A27 | GET `/api/v1/cases/{case_id}/retrieval/{run_id}` | — → RetrievalResponse | knowledge:read / AI | Scope/pinning enforced; metadata/ranks/scores/citation, no passage text |
| A28 | POST `/api/v1/cases/{case_id}/ai/drafts` | ExecuteAdvisoryRequest → AIDraftResponse | ai:write / AI | retrieval_run_id + one of four TaskType values; advisory only; validation rejection remains explicit |
| A29 | GET `/api/v1/tasks/{task_id}` | — → AsyncTaskResponse | case:read on task case | Result/attempt/retry metadata omitted; no percent progress |
| A30 | GET `/api/v1/cases/{case_id}/tasks` | — → AsyncTaskResponse[] | case:read | Persisted task status list; not complete processing output discovery |
| A31 | GET `/api/v1/queue` | status?, assigned_to? → QueueItemResponse[] | review:read | Facility-filtered; limit50/offset0 service defaults not exposed |
| A32 | POST `/api/v1/cases/{case_id}/review/queue` | EnterQueueRequest → QueueItemResponse, 201 | review:write / AI | Requires REVIEW_PENDING, optional same-case encounter |
| A33 | POST `/api/v1/queue/{case_id}/assign` | AssignReviewerRequest → QueueItemResponse | review:assign / AI | reviewer_id, expected_version≥1; active review:write/scoped eligibility |
| A34 | POST `/api/v1/queue/{case_id}/reassign` | ReassignReviewerRequest → QueueItemResponse | review:assign / AI | reviewer_id, reason 1–1000, expected_version≥1 |
| A35 | POST `/api/v1/cases/{case_id}/review/start` | VersionRequest → QueueItemResponse | review:write / AI + assignment/assign privilege | Queue version≥1; ASSIGNED→IN_REVIEW |
| A36 | GET `/api/v1/cases/{case_id}/review/workspace` | — → dict[str,Any] | review:read / AI + assignment/assign privilege | Actual structured aggregate, not unspecified arbitrary data; omissions listed below |
| A37 | POST `/api/v1/drafts/{draft_id}/accept` | DraftActionRequest → DraftActionResponse | review:write / AI + assignment | DRAFT + IN_REVIEW + draft/queue versions; AI validation/policy rejection sets REJECTED and blocks this action |
| A38 | POST `/api/v1/drafts/{draft_id}/reject` | RejectDraftRequest → DraftActionResponse | review:write / AI + assignment | Same versions; rationale1–4000; human status REJECTED |
| A39 | POST `/api/v1/drafts/{draft_id}/edit` | EditDraftRequest → DraftActionResponse | review:write / AI + assignment | Nonempty dict, optional rationale≤4000; immediately APPROVED; edited content stored separately |
| A40 | POST `/api/v1/cases/{case_id}/review/decision` | ReviewDecisionRequest → ReviewDecisionResponse | review:write / AI + assignment | case/queue/draft versions≥1; APPROVE/REFER need approved draft; REJECT needs rejected draft plus rationale; other enum values rejected |
| A41 | POST `/api/v1/cases/{case_id}/escalation` | CreateEscalationRequest → EscalationResponse, 201 | escalation:write / AI + assignment | reason 1–4000, case/queue versions; active review only |
| A42 | POST `/api/v1/escalations/{escalation_id}/resolve` | ResolveEscalationRequest → EscalationResponse | escalation:write / AI + assignment | notes 1–4000 and case/queue versions; returns case/queue to review |
| A43 | POST `/api/v1/cases/{case_id}/referral` | PrepareReferralRequest → ReferralPackageResponse, 201 | referral:write / RF | 1–100 selected same-case evidence UUIDs; current approved decision/draft version checked at prepare |
| A44 | POST `/api/v1/referrals/{package_id}/finalize` | — → ReferralPackageResponse | referral:write / RF | DRAFT→FINALIZED; no current approval/version revalidation here |
| A45 | POST `/api/v1/referrals/{package_id}/handoff` | InitiateHandoffRequest → HandoffResponse, 201 | handoff:write / RF | Active recipient_id; finalized package, REVIEWED case; idempotent package+recipient+case |
| A46 | POST `/api/v1/handoffs/{handoff_id}/send` | SendHandoffRequest → HandoffResponse | handoff:write / RF | expected_version≥1; enqueues READY, never synchronous transmission success |
| A47 | POST `/api/v1/handoffs/{handoff_id}/acknowledge` | AcknowledgeHandoffRequest → HandoffResponse | handoff:write / RF + sender or recipient:manage | reference 1–500, version; only after send; manual acknowledgment evidence |
| A48 | POST `/api/v1/handoffs/{handoff_id}/complete` | CompleteHandoffRequest → HandoffResponse | handoff:write / RF + sender or recipient:manage | handoff/case versions; ACKNOWLEDGED→COMPLETED, case completed |
| A49 | GET `/api/v1/recipients` | — → RecipientResponse[] | handoff:read | Active global list id/name/type; no contact/configuration CRUD |
| A50 | POST `/api/v1/audio/speech` | TextToSpeechRequest → binary audio | Authenticated user only | Nonblank text ≤4096, optional voice; not audio intake or patient-scoped |
| A51 | GET `/api/v1/health/live` | — → {status:ok} | Public | Process only |
| A52 | GET `/api/v1/health/ready` | — → status/checks/latency | Public | Bounded DB, Redis, blob checks, 200/503; no provider benchmark |

### Contract details and failure presentation

Common envelope: `{"error":{"code":"…","message":"…","correlation_id":"…"}}`. Verified exception types map authentication 401, authorization/consent 403, object not found 404, conflict/optimistic lock 409, request/domain/state validation 422, too large 413, extension/MIME 415, storage/scanner unavailable 503 and unexpected/audit failure 500. Object denial may intentionally return 404. Request validation summarizes errors without field details or raw inputs: frontend must provide local field feedback and must not assume the server returns a field-error dictionary. No automatic replay of non-idempotent writes on unknown outcomes.

Consent schemas allow arbitrary purpose/notice strings; policy-enforced workflow purposes above are exact. Missing consent IDs in capture/withdraw raise ordinary ValueError and reach 500, not a well-defined 404. Invalid processing strings are converted to enum inside handlers and may reach 500. These are backend contract gaps, not frontend error messages to invent.

`EvidenceResponse` has **12** fields: evidence_id, case_id, encounter_id, modality, state, content_type, size_bytes, original_filename, source_language, created_by, created_at, provenance. Checksum/storage key are internal, not response fields. Supported default extensions: `.pdf,.docx,.txt,.jpg,.jpeg,.png,.mp3,.wav,.m4a,.ogg`; maximum **52,428,800 bytes (50 MiB)**; configurable read URL TTL default **15 minutes**. No settings discovery API verifies effective runtime values. Upload’s source_language is not a multipart field. Do not add required patient demographics, report dates or language fields to the payload without a contract.

Processors: `document_ocr`, `speech_transcription`, `language_normalization`, `candidate_extraction`. File language normalization and every candidate extraction require `parameters.source_processing_run_id`; target language defaults `en`. Source must belong to same evidence, be COMPLETED and be OCR/STT/language as applicable. Processing response ID is distinct from task ID and extraction ID. A synchronous provider failure may return a FAILED run without HTTP failure. The processing worker explicitly raises on FAILED results; durable executor records task failure/retry separately. Its business transaction commits only after handler success, so failed-run artifact persistence across async rollback needs direct verification. Task success is not clinical verification; display task and persisted run states separately. Recalling failed idempotent processor executions can return the same failed run rather than retrying the provider.

Four AI task values: `reviewer_note_draft`, `evidence_summary`, `structured_case_summary`, `clarification_support`. All currently use a bounded advisory output shape (summary, claims with status/source identifiers, missing_information_ids, limitations), not autonomous clinical commands. Provenance source IDs may refer to derived/retrieved content; they must be resolved to original evidence/approved knowledge through a verified locator contract, not guessed from UUID shape.

### Reviewer workspace contract actually observed

`WorkspaceService.get_reviewer_workspace` returns case and queue versions; encounters; original evidence with origin/text/download route; derived processing runs with OCR region boxes/page number, transcript intervals/speaker and candidates/value/status/provenance; latest structuring timeline/missing/conflicts/questions; retrieval run/citations; AI drafts/raw content/version/reviewer state/provenance and policy checks; existing human note, review decisions, escalation summaries, referral and handoff summaries.

It omits OCR table cells/dimensions/reading order/confidence, candidate normalized values/confidence/ExtractionRun ID, language results, full source passages, latest edited human draft content/edit history, and usable handoff versions/timestamps/failure details. Its return is an untyped dictionary, and access requires a queue plus assigned reviewer/assign privilege and AI consent. It cannot substitute for an intake evidence-list/results contract or an operational handoff reader.

<a id="audit-section-7"></a>

## 7. Frontend route and module inventory

Evidence paths below are relative to `frontend/src`. `L` means local useState/form validation plus timer-disconnected result; `S` means static representation; neither is a durable workflow. Current pages do not declare/enforce roles. Intended roles here derive from the matching backend permissions, pending DEC-02.

| Route | Page/components and actual fields/actions | Validation, navigation, states and limitation |
|---|---|---|
| `/` | `app/page.tsx`, `RootPage` → redirect `/login` | Implemented and verified entry navigation; no session bypass |
| `/login` | `(auth)/login/page.tsx`; BrandPanel, LoginForm, PasswordField | Email regex, required password, visibility toggle, local submitting/error/disconnected state; forgot link; no token/session/login redirect |
| `/login/forgot-password` | `(auth)/login/forgot-password/page.tsx` | Email/local validation and submitted message; no reset request. Backend recovery absent, not merely awaiting integration |
| `/dashboard` | `(shell)/dashboard/page.tsx`, shell welcome card | S; no actual workload, role actions, totals or recovery summaries |
| `/cases` | CaseList, StatusBadge; search, filter/sort controls, new-case link; columns ID/title/patient identifier/priority/status | Search state only; no records/query; filter/sort no meaningful handlers, pagination disabled 0/0. Unsupported title/priority semantics |
| `/cases/new` | CaseForm; title, patientId “MRN or distinct ID”, routine/urgent/stat priority, consentVerified | L; mandatory unsupported fields and checkbox; cancel→cases; no subject UUID/facility/active consent workflow |
| `/cases/[id]` | CaseDetails; overview/history, fixed “Under Review” placeholder | S; page does not consume dynamic params. No case, encounter, narrative, evidence, reviewer or history data |
| `/evidence` | TextEvidenceForm, FileEvidenceForm, EvidenceMetadataCard, ProcessingTriggerForm, TaskStatusPanel; submit/record/process tabs | L text/case/consent nonblank and text≤20000, optional sourceLanguage; single file/extension checks, raw IDs, no encounter or local file-size rejection. Metadata/download disabled; task panel empty. Processor options include unsupported structure_extraction/clinical_intelligence, omit language_normalization/candidate_extraction |
| `/intelligence` | EvaluationTrigger, StructuringSummaryCard, TimelineList, ConflictList, MissingInfoList, RetrievalForm, AIDraftForm; six tabs | L case/extraction/run IDs; retrieval query/corpus/mode/top_k and four real AI tasks. Static “no conflicts/missing” before evaluation can imply false negatives. Subtitle claims verified advisory drafts. No results/evidence links |
| `/review` | ReviewQueueList/Badge, EnterQueueForm, Assign/ReassignReviewerForm, StartReviewForm, ReviewWorkspacePanel, DraftAccept/Reject/EditForm, ReviewDecisionForm; queue/actions/decisions tabs | L raw UUIDs and manual versions default1; parseInt≥1 can accept fractional-looking strings; reasons limits1000/4000. Queue filters local and refresh inert. Edit JSON parses but not nonempty object. All five decision enum values displayed although two unsupported here. No actual workspace/assignment/history |
| `/escalations` | EscalationForm, EscalationResolveForm, EscalationStatusBadge | L raw IDs/versions, reasons/notes≤4000; enum legend includes ACKNOWLEDGED without action; no case ownership/history/read list |
| `/handoff` | ReferralPrepare/FinalizeForm, HandoffInitiate/Send/Acknowledge/CompleteForm, RecipientPanel; package/lifecycle/recipient tabs | L raw IDs, comma-separated evidence≤100, versions default1; reference lacks server max500. No selected case/evidence/recipient propagation, package preview, lifecycle polling or ack ownership |
| `/design-system` | `app/design-system/page.tsx`, shared UI examples | S with working local dialog/dropdown/tabs primitives; colors/typography/buttons/badges/form examples/skeleton/empty state. “First Name” example is not patient intake; example actions have no business effect |

Common shell: `AppSidebar` has seven unconditional items (Overview, Cases, Evidence, Clinical Intelligence, Review Workspace, Escalations, Referral & Handoff); `AppHeader` search has no action and account/preferences/logout are disabled. `AppShell` collapses sidebar and opens/closes mobile drawer with Escape/scroll lock, but the offscreen drawer remains mounted as a modal without explicit focus trapping/inertness/restoration. No frontend route protection/session provider, API client, integration hooks, middleware, dedicated loading/error/not-found route files or frontend tests were found.

Shared primitives: badge, button, card, dialog, dropdown-menu, empty-state, form-field, helper-text, input, label, select, separator, skeleton, table, tabs, textarea, tooltip (**17 files**). Base UI provides several interactive primitives; thin wrappers alone do not establish page accessibility. Login associates invalid/error descriptions; many workflow forms only render error paragraphs. JSON edit uses `font-mono`, contrary to Times New Roman throughout. CSS defines established clinical navy/teal/status tokens and serif body/control typography; preserve these rather than redesigning.

<a id="audit-section-8"></a>

## 8. Backend implementation status matrix

This groups section 9’s individually traceable capabilities by implementation depth. A whole module cannot inherit “complete” from one route or test.

| Area / capability IDs | Status and proven behavior | Remaining boundary |
|---|---|---|
| B-001–004 | Login/session/bootstrap Implemented and verified; permission/facility machinery Partially implemented | No staff lifecycle; clinical seed/scope concerns B-003/B-057 remain separate |
| B-005–010 | Password lifecycle Unsupported; staff/facility Documented only; identity/disclosure incomplete; consent lifecycle Partially implemented | Subjects are users, no patient-name or disclosure/data-class contract, no consent reads/scoped administration |
| B-011–017 | Create/read/history/encounters/services exist; generic transitions, narrative/upload partial; case browsing Unsupported | Case workflow cannot be built from current form fields; no automatic complete intake pipeline |
| B-018–022 | Storage adapter exists; scan unsupported, evidence/provenance contracts partial, deletion documented only | Upload-to-READY and complete intake/read/delete contracts blocked |
| B-023–029 | OCR/STT/language/extraction/run execution/task/recovery code exists, all Partially implemented as end-user workflows | Demo-only fields, missing result identifiers/reads, unreliable retry after persisted failure |
| B-030–034 | Conservative structuring/missing/questions partial; clarification partial internal service only | Cross-evidence conflicts, date-type semantics, answer/stop/correction and second round absent |
| B-035–039 | Internal knowledge, retrieval and AI/policies/version persistence substantive but partially exposed | No governed source/corpus UI contract or complete metadata reader; existing REJECTED/DRAFT review gate must remain visible |
| B-040–047 | Manual note unsupported; queue/assignment/workspace/actions/decision/history/invalidation partial | Qualified approval and material-change safety gaps are backend obligations |
| B-048–054 | Review-stage escalation/package/demo send/ack code exists, operational ownership/recipient/timeout incomplete | No early escalation/live handoff/followup and durable reads |
| B-055–060 | Append-only audit/health source implemented; audit view, retention absent; isolation partial; TTS authenticated | Platform privacy/clinical permission decisions remain |
| B-061–065 | Real-time Unsupported; facility configuration documented only; urgency deliberately unsupported; operational monitoring partial; export Unsupported | Poll persisted states only; retain deferred clinical/interoperability scope |

<a id="audit-section-9"></a>

## 9. Backend–frontend gap matrix

Each row is one meaningful capability, not one page or endpoint. Exactly **65 B rows** constitute the backend capability inventory, including documented/unsupported/unverified items; **three F rows** cover frontend foundations. Counts must use the primary classification column once per row. Security/contract/product gaps may also have frontend work, but are not double-counted as “Frontend gap”. Section 10 maps the actions to FE requirements; section 17 defines BG dependencies.

| Feature ID | Module | Capability | Backend status | Backend evidence | Frontend status | Frontend evidence | Gap classification | Required action | Priority |
|---|---|---|---|---|---|---|---|---|---|
| B-001 | Auth | Password login | Implemented and verified | E-02 AuthService.login; A01 | UI only / local state | LoginForm | Frontend gap | [FE-001](#fe-001) session-ready login specification | P0 |
| B-002 | Auth | JWT expiry/revocation/profile/logout | Implemented and verified | E-02 SessionRepository; A02/A03 | Missing | AppHeader disabled logout; no session | Frontend gap | [FE-001](#fe-001) expiry/logout/error flow | P0 |
| B-003 | Access | Permission/facility-aware action boundaries | Partially implemented | E-03 AuthorizationPolicy; additive role seeds | Missing | AppSidebar unconditional | Security or permission gap | [FE-002](#fe-002); BG-020; DEC-02/03 | P0 |
| B-004 | Admin | First system-wide admin bootstrap | Implemented and verified | E-03 FirstAdminBootstrapService, CLI/tests | Missing | No admin route | No gap identified | Retain CLI-only bootstrap, no public wizard | P3 |
| B-005 | Auth | Password reset/refresh/account recovery | Unsupported | E-01 complete routers; E-02 auth schemas | UI only / local state | forgot-password page | Cross-layer gap | [FE-001](#fe-001) label unavailable; BG-021 if required | P2 |
| B-006 | Admin | Staff lifecycle/individual provisioning/roles | Documented only | P FR-029; U administrator role; E-03 user records only | Missing | No directory/admin page | Backend gap | BG-015 then [FE-027](#fe-027); DEC-04 | P2 |
| B-007 | Facility | Facility entity/membership/departments | Documented only | P FR-033; E-03/E-05 nullable UUIDs only | Missing | No facility UI | Backend gap | BG-015; department scope not assumed | P2 |
| B-008 | Identity | Synthetic subject/name/lookup/data-class validation | Partially implemented | E-05 CreateCaseRequest; E-04 subject user FK | UI only / local state | CaseForm MRN field | Cross-layer gap | BG-001; [FE-003](#fe-003); DEC-01 | P0 |
| B-009 | Consent | Purpose-specific request/capture/withdraw | Partially implemented | E-04 ConsentService; A04–06 | Missing | CaseForm checkbox only | Cross-layer gap | [FE-006](#fe-006); BG-003 | P0 |
| B-010 | Intake | Purpose/prototype disclosure and permitted class | Documented only | P FR-002/005; E-04 no disclosure payload | Missing | No notice/acknowledgement workflow | Backend gap | BG-003 then [FE-006](#fe-006) | P0 |
| B-011 | Cases | Create case against active consent | Implemented and verified | E-05 create_case; A07 | UI only / local state | CaseForm | Frontend gap | [FE-003](#fe-003) replace unsupported payload fields | P0 |
| B-012 | Cases | Case/patient list/search/filter/pagination | Unsupported | E-01 routes; E-05 CaseRepository lacks list | UI only / local state | CaseList | Backend contract gap | BG-002 then [FE-004](#fe-004) | P1 |
| B-013 | Cases | Case read and lifecycle history | Implemented and verified | E-05 get_case/get_state_history; A08/A10 | UI only / local state | CaseDetails ignores route ID | Frontend gap | [FE-004](#fe-004) case-specific details/history | P1 |
| B-014 | Cases | Lifecycle/closure and ownership transitions | Partially implemented | E-05 transition_state; CaseStateMachine | Missing | No lifecycle actions | Security or permission gap | BG-011; [FE-004](#fe-004) prohibit generic clinical transitions | P0 |
| B-015 | Intake | Encounter creation/list/association | Implemented and verified | E-05 EncounterService; A11/A12 | Missing | No encounter form/details | Frontend gap | [FE-005](#fe-005) | P1 |
| B-016 | Intake | Verbatim narrative/source language | Partially implemented | E-06 register_text_evidence TEXT; A13 | UI only / local state | TextEvidenceForm | Cross-layer gap | BG-005; [FE-007](#fe-007) context/correct validation | P1 |
| B-017 | Evidence | One-file upload validation/case association | Partially implemented | E-06 file service/validator; A14 | UI only / local state | FileEvidenceForm | Cross-layer gap | [FE-008](#fe-008); BG-004/005 | P1 |
| B-018 | Storage | Original storage and secure download | Partially implemented | E-07 AzureBlobProvider; A16 READY guard | UI only / local state | disabled EvidenceMetadataCard | Cross-layer gap | [FE-010](#fe-010); BG-004; consent/read policy DEC-03 | P1 |
| B-019 | Evidence | Real scanning/quarantine completion | Unsupported | E-06 main NoOpScanner PENDING | Missing | No readiness explanation | Backend gap | BG-004 before file processing; [FE-008](#fe-008)/011 | P0 |
| B-020 | Evidence | Case evidence/raw artifact list and details | Partially implemented | E-06 list_for_case unregistered; A15/A36 | UI only / local state | MetadataCard no selection | Backend contract gap | BG-005; [FE-009](#fe-009) | P1 |
| B-021 | Evidence | Exact page/region/cell/span/audio provenance | Partially implemented | E-08–10 processing models; E-14 workspace omissions | Missing | No source inspector | Cross-layer gap | BG-005/007; [FE-010](#fe-010)/013/019 | P1 |
| B-022 | Evidence | File deletion/derived cleanup | Documented only | P FR-032; E-06 delete states; E-07 low-level delete | Missing | No deletion UI | Backend gap | BG-018; [FE-028](#fe-028) blocked | P0 |
| B-023 | Processing | OCR/multipage/tables | Partially implemented | E-08 DocumentProcessor/Azure OCR; A17–19 | UI only / local state | OCR trigger only | Cross-layer gap | BG-004/005; [FE-011](#fe-011)/013 | P1 |
| B-024 | Processing | STT interval/replay/correction | Partially implemented | E-09 SpeechProcessor/Azure STT | UI only / local state | Audio file mode; no transcript | Cross-layer gap | BG-005/007; [FE-010](#fe-010)/013 | P1 |
| B-025 | Processing | Language detection/translation/normalization | Partially implemented | E-10 demo providers always wired | Missing | Trigger lacks language mode | Cross-layer gap | [FE-013](#fe-013); BG-007; DEC-06 | P1 |
| B-026 | Processing | Candidate/report/demographic extraction | Partially implemented | E-10 fever/date-only DemoExtractionProvider | Missing | Unsupported structure_extraction option | Cross-layer gap | [FE-013](#fe-013); BG-007 | P1 |
| B-027 | Processing | Valid processor execution/parameters/status | Partially implemented | E-10 ProcessingService; A17–19 | UI only / local state | ProcessingTriggerForm wrong types | Cross-layer gap | [FE-011](#fe-011); BG-006 | P1 |
| B-028 | Tasks | Task status and durable output discovery | Partially implemented | E-18 task result stored/omitted; A18/A29/30 | UI only / local state | TaskStatusPanel | Backend contract gap | BG-006; [FE-012](#fe-012) | P1 |
| B-029 | Recovery | Retry/idempotency/stale task/outbox | Partially implemented | E-18 executor/recovery; processor failed-run reuse | Missing | No recovery controls | Backend contract gap | BG-006; [FE-012](#fe-012); no invented retry API | P1 |
| B-030 | Structuring | Timeline/date distinctions | Partially implemented | E-11 TemporalNormalizer; A21 | UI only / local state | TimelineList empty | Cross-layer gap | [FE-014](#fe-014); BG-007 | P1 |
| B-031 | Structuring | Conflicting facts/candidate preservation | Partially implemented | E-11 onset-only policy/link table; A22 omits links | UI only / local state | ConflictList static | Cross-layer gap | [FE-014](#fe-014); BG-007 | P1 |
| B-032 | Structuring | Checklist/missing/unreadable/unverified | Partially implemented | E-11 MissingInfoEvaluator; A23/A25 | UI only / local state | MissingInfoList/summary | Cross-layer gap | [FE-015](#fe-015); approved checklist DEC-06/BG-019 | P1 |
| B-033 | Structuring | Bounded follow-up question display | Partially implemented | E-11 first round, demo maximum 3, maxround2; A24 | UI only / local state | Intelligence questions placeholder | Cross-layer gap | [FE-015](#fe-015); BG-008 for interaction | P1 |
| B-034 | Clarification | Selection/answers/rounds/stop/return | Partially implemented | E-15 ClarificationService unregistered/incomplete | Missing | Decision selector only | Backend gap | BG-008; [FE-022](#fe-022) dependent | P1 |
| B-035 | Knowledge | Governed source/version ingestion/publication | Partially implemented | E-12 KnowledgeService internal, no routes | Missing | No knowledge administration | Backend contract gap | BG-019; [FE-016](#fe-016)/028; admin UI optional DEC-09 | P2 |
| B-036 | Retrieval | Pinned hybrid/dense/sparse retrieval | Partially implemented | E-12 RetrievalService; A26/A27; no passage read | UI only / local state | RetrievalForm | Cross-layer gap | [FE-016](#fe-016); BG-019 | P1 |
| B-037 | AI | Four bounded advisory draft tasks | Implemented and verified | E-13 workflow/service/schema; A28 | UI only / local state | AIDraftForm | Frontend gap | [FE-017](#fe-017) advisory results and context | P1 |
| B-038 | AI safety | Validation/abstention/policy rejection gate | Implemented and verified | E-13 AIService sets REJECTED; E-15 _locked_context requires DRAFT | UI only / local state | AI placeholder “verified” copy | Frontend gap | [FE-017](#fe-017)/020 preserve rejected-output gate and distinguish validation from human verification | P0 |
| B-039 | AI trace | Model/prompt/retrieval/policy/case/note versions | Partially implemented | E-13 AIRunORM; A28 lacks metadata/version | Missing | No trace/version panel | Backend contract gap | BG-019; [FE-017](#fe-017)/021 | P1 |
| B-040 | Review | Manual note/template fallback during outage | Unsupported | P NFR-001; E-15 ReviewerNoteORM unused creation | Missing | No human-note editor | Backend gap | BG-009; [FE-022](#fe-022) | P1 |
| B-041 | Review | Queue display/filters | Partially implemented | E-14 list_queue; A31 fixed first 50 | UI only / local state | ReviewQueueList | Cross-layer gap | [FE-018](#fe-018); BG-022 pagination | P1 |
| B-042 | Review | Assign/reassign/start review | Implemented and verified | E-14 ReviewService; A33–35 | UI only / local state | Raw-ID/version forms | Frontend gap | [FE-018](#fe-018); directory BG-015 | P1 |
| B-043 | Review | Case workspace/source/derived/AI separation | Partially implemented | E-14 WorkspaceService; A36 | UI only / local state | ReviewWorkspacePanel empty | Cross-layer gap | [FE-019](#fe-019); BG-005/010 | P0 |
| B-044 | Review | Accept/reject/edit draft | Partially implemented | E-15 DraftReviewService; A37–39 | UI only / local state | Draft action forms | Cross-layer gap | [FE-020](#fe-020); BG-010/011 | P0 |
| B-045 | Review | Explicit decision/disposition | Partially implemented | E-15 ReviewDecisionService; A40 | UI only / local state | Unsupported decision options | Cross-layer gap | [FE-020](#fe-020); BG-008/011 | P0 |
| B-046 | Review | Note edit/version history/diff | Partially implemented | E-15 DraftEditVersionORM, no read route | Missing | No history/diff | Backend contract gap | BG-010; [FE-021](#fe-021) | P1 |
| B-047 | Review | Material-change invalidation/reopen | Partially implemented | E-06 postapproval evidence guard; E-15 DRAFT-only edit | Missing | No reapproval flow | Backend gap | BG-010; [FE-021](#fe-021) | P0 |
| B-048 | Escalation | Review-stage manual escalation/resolve | Implemented and verified | E-16 EscalationService; A41/A42 | UI only / local state | Escalation/ResolveForm | Frontend gap | [FE-023](#fe-023) context/current versions | P0 |
| B-049 | Escalation | Intake bypass/ownership/ack/history | Partially implemented | P FR-024; E-16 review-only; no ACK route | Missing | No ownership/history | Backend gap | BG-012; [FE-023](#fe-023); DEC-05 | P0 |
| B-050 | Referral | Approved package/select/finalize/preview | Partially implemented | E-17 ReferralPackageService; A43/A44 | UI only / local state | Raw evidence IDs/finalize | Cross-layer gap | [FE-024](#fe-024); BG-013 | P1 |
| B-051 | Recipients | Active recipient selection/configuration | Partially implemented | E-17 A49 list only, global RecipientORM | UI only / local state | RecipientPanel empty | Cross-layer gap | [FE-026](#fe-026); BG-016; DEC-08 | P2 |
| B-052 | Handoff | Initiate/send/demo delivery/failure | Partially implemented | E-17/A45/A46; E-18 demo-only worker | UI only / local state | Initiate/SendForm | Cross-layer gap | [FE-025](#fe-025); BG-014 | P1 |
| B-053 | Handoff | Acknowledge then complete | Implemented and verified | E-17 sender/manager guard; A47/A48 | UI only / local state | Ack/CompleteForm | Frontend gap | [FE-025](#fe-025) separate stages/current versions | P1 |
| B-054 | Handoff | Receipt/rejection/timeout/followup ownership | Documented only | P FR-027/028; E-17 missing operations | Missing | No pending followup UI | Backend gap | BG-014; [FE-025](#fe-025); DEC-08 | P1 |
| B-055 | Audit | Append-only actor/action/target/trace/outcome | Implemented and verified | E-19 repository/models/0013/R6 tests | Missing | No audit page | No gap identified | Keep backend control; UI read is B-056 | P0 |
| B-056 | Audit | Authorized audit browsing | Documented only | P FR-029/031; E-01 no audit route/permission | Missing | No audit UI | Backend contract gap | BG-017; [FE-028](#fe-028) | P2 |
| B-057 | Privacy | Scope/isolation/consent/read/delivery boundaries | Partially implemented | E-03 policy; E-04 consent; E-18 delivery actor discarded | Missing | No scope/consent failure UX | Security or permission gap | BG-003/014/020; [FE-002](#fe-002)/006/029 | P0 |
| B-058 | Retention | All-artifact lifecycle/deletion verification | Documented only | P FR-032/NFR-009; E-01 no lifecycle task/API | Missing | No retention page | Backend gap | BG-018; [FE-028](#fe-028); DEC-10 | P0 |
| B-059 | Operations | Liveness/readiness/errors/trace | Implemented and verified | E-21 A51/A52; core errors/correlation | Missing | No common server-error UI | Frontend gap | [FE-029](#fe-029) common state/error mapping | P0 |
| B-060 | Audio | Authenticated text-to-speech | Implemented and verified | E-22 SpeechService; A50 | Missing | No playback/read-aloud control | Frontend enhancement | [FE-031](#fe-031) conditional accessibility option | P3 |
| B-061 | Progress | WebSocket/SSE/realtime subscription | Unsupported | E-01/E-18 no registered realtime mechanism | Missing | No subscription logic | No gap identified | Use task polling contract; realtime not required | P3 |
| B-062 | Configuration | Facility languages/fields/workflow/retention | Documented only | P FR-033/NFR-010; E-01 no config API | Missing | Preferences disabled | Backend gap | BG-019; [FE-028](#fe-028); DEC-09 | P2 |
| B-063 | Clinical scope | Local-policy urgency/final clinical priority | Unsupported | P FR-023/025 conditional; E-05 no case priority | UI only / local state | CaseForm mandatory priority | Product decision required | [FE-003](#fe-003)/029 Unassigned; DEC-05, no policy invention | P0 |
| B-064 | Operations | Monitoring/incident/recovery controls | Partially implemented | E-21 logs/probes/scripts; no metrics/exporter | Missing | No operations UI | No gap identified | Backend/platform concern; DEC-12; UI only verified failures | P2 |
| B-065 | Exchange | Export/interoperability/live external referral | Unsupported | P deferred scope; export consent enum only | Missing | No export/integration page | No gap identified | Explicitly defer; no fabricated export action | P3 |
| F-001 | Entry | Root shows login first | Implemented and verified | Auth routes support eventual login | Implemented and verified | RootPage redirect | No gap identified | Preserve `/`→`/login`, [FE-001](#fe-001) | P0 |
| F-002 | Foundation | Responsive/accessibility/design consistency | Unverified | P NFR-007; no browser evidence | Partially implemented | AppShell/UI/globals.css | Frontend gap | [FE-029](#fe-029) fix focus/errors/serif consistency | P0 |
| F-003 | Overview | Useful permission-aware dashboard | Unverified | No aggregate dashboard contract | UI only / local state | dashboard static card | Frontend enhancement | [FE-030](#fe-030) action links, no invented totals | P2 |

<a id="audit-section-10"></a>

## 10. Missing and incomplete frontend requirements

The metadata row below and its same-ID detail in section 15 jointly define each requirement. “Source” identifies actual PRD IDs; “task” means a user instruction in this audit rather than an invented PRD identifier. Every FE requirement inherits the shared UI/acceptance rules in §15.1 and the role restrictions in §13. Backend-gap dependents are **blocked**, not a request to fabricate a screen that appears operational.

| Requirement / module and title | Classification | Priority and justification for P0/P1 | Source | Backend status / current frontend status | Evidence and capability links |
|---|---|---|---|---|---|
| [FE-001](#fe-001) Auth: login/session/logout/recovery boundary | Frontend gap | P0 — establish real access before protected workflow | FR-029; SEC-001/005; task root-login | Implemented and verified for login/session; recovery Unsupported / UI only / local state | E-02,E-23; B-001/002/005/F-001 |
| [FE-002](#fe-002) Foundation: permission-aware shell and scope | Security or permission gap | P0 — prevent misleading access and clinical authority | FR-029; SEC-001/009 | Partially implemented / Missing | E-03,E-23; B-003/057 |
| [FE-003](#fe-003) Intake: subject selection and contract-aligned case creation | Cross-layer gap | P0 — required identity/consent anchors for every dependent module | FR-001/023; task patient name | Partially implemented identity; Implemented and verified creation / UI only / local state | E-04/05/23; B-008/011/063 |
| [FE-004](#fe-004) Cases: browse/details/history/context | Frontend gap | P1 — case recovery and cross-module navigation | FR-001; NFR-003/004 | Implemented and verified details, Unsupported list / UI only / local state | E-05,E-23; B-012/013/014 |
| [FE-005](#fe-005) Intake: encounter creation/details | Frontend gap | P1 — preserve interaction and evidence association | FR-001/003/012 | Implemented and verified / Missing | E-05,E-23; B-015 |
| [FE-006](#fe-006) Consent: disclosure/request/capture/status/withdraw | Cross-layer gap | P0 — purpose/data restrictions precede evidence/AI/referral | FR-002/005/029; SEC-009 | Partially implemented / Missing | E-04,E-23; B-009/010/057 |
| [FE-007](#fe-007) Intake: verbatim text narrative | Cross-layer gap | P1 — primary manual intake must preserve original | FR-003/005/008; NFR-001/003 | Partially implemented / UI only / local state | E-06,E-23; B-016 |
| [FE-008](#fe-008) Reports: validated case-associated upload | Cross-layer gap | P1 — primary sample-report input; readiness blocker is P0 | FR-006/009/010/011; SEC-003 | Partially implemented / UI only / local state | E-06/07/23; B-017/019 |
| [FE-009](#fe-009) Evidence: inventory/metadata/workspace | Backend contract gap | P1 — accepted evidence must remain findable after refresh | FR-007/018; NFR-003/004 | Partially implemented / UI only / local state | E-06/14/23; B-020 |
| [FE-010](#fe-010) Evidence: source preview/provenance/audio replay | Cross-layer gap | P1 — qualified review requires inspectable originals | FR-004/009/010/018 | Partially implemented / Missing | E-07–10/14/23; B-018/021/024 |
| [FE-011](#fe-011) Processing: valid step controls/run status | Cross-layer gap | P1 — connect evidence to derived information accurately | FR-007/010; NFR-002/003 | Partially implemented / UI only / local state | E-08–10/18/23; B-023/026/027 |
| [FE-012](#fe-012) Tasks: polling/failure/recovery | Backend contract gap | P1 — long tasks must not silently fail or lose result linkage | NFR-001/002/003/005 | Partially implemented / UI only / local state | E-18,E-23; B-028/029/061 |
| [FE-013](#fe-013) Extraction: original/normalized fields and uncertainty | Cross-layer gap | P1 — avoid treating candidates as verified facts | FR-007/008/009/010; NFR-008 | Partially implemented / Missing | E-08–10/14/23; B-021/023–026 |
| [FE-014](#fe-014) Intelligence: timeline and conflicting candidates | Cross-layer gap | P1 — preserve chronology and contradictions for reviewer | FR-012/013/018 | Partially implemented / UI only / local state | E-11,E-23; B-030/031 |
| [FE-015](#fe-015) Intelligence: checklist gaps and follow-up display | Cross-layer gap | P1 — missing information must remain unknown | FR-014/015/016 | Partially implemented / UI only / local state | E-11,E-23; B-032/033 |
| [FE-016](#fe-016) Knowledge: retrieval controls/citations | Cross-layer gap | P1 — visible approved context for evidence-linked draft | FR-017/018/030 | Partially implemented / UI only / local state | E-12,E-23; B-035/036 |
| [FE-017](#fe-017) AI: advisory draft/result/safety/trace | Frontend gap | P1 — present bounded drafts without clinical authority | FR-017/018/023/030 | Implemented and verified generation, partial metadata / UI only / local state | E-13,E-23; B-037–039 |
| [FE-018](#fe-018) Review: queue/assignment/start | Frontend gap | P1 — connect cases to authorized review ownership | FR-019/029 | Partially implemented queue; verified commands / UI only / local state | E-14,E-23; B-041/042 |
| [FE-019](#fe-019) Review: connected evidence workspace | Cross-layer gap | P0 — source/edited content fidelity is prerequisite to approval | FR-018/019; NFR-004 | Partially implemented / UI only / local state | E-14/15/23; B-043 |
| [FE-020](#fe-020) Review: guarded edit/reject/approve/disposition | Cross-layer gap | P0 — enforce explicit qualified human approval | FR-019/020/021/026; SEC-001 | Partially implemented / UI only / local state | E-15,E-23; B-038/044/045 |
| [FE-021](#fe-021) Review: versions/diff/invalidation/reapproval | Backend contract gap | P0 — stale or changed content must not retain approval | FR-019/021/022/030 | Partially implemented / Missing | E-15,E-23; B-039/046/047 |
| [FE-022](#fe-022) Review/intake: manual fallback and clarification lifecycle | Backend gap | P1 — core workflow needs AI-outage and clarification recovery | FR-015/016/019; NFR-001 | Unsupported manual note; partial clarification / Missing | E-15,E-23; B-034/040 |
| [FE-023](#fe-023) Escalation: human action, ownership and resolution | Frontend gap | P0 — manual escalation must remain available independent of AI | FR-024; NFR-001 | Verified review action; partial bypass/ownership / UI only / local state | E-16,E-23; B-048/049 |
| [FE-024](#fe-024) Referral: approved-content package/evidence selection | Cross-layer gap | P1 — referral must carry current approved content | FR-026/027 | Partially implemented / UI only / local state | E-17,E-23; B-050 |
| [FE-025](#fe-025) Handoff: delivery/acknowledgement/closure/followup | Cross-layer gap | P1 — transmission is not completed responsibility transfer | FR-027/028; NFR-003 | Partially implemented / UI only / local state | E-17/18/23; B-052–054 |
| [FE-026](#fe-026) Recipients: selection and bounded administration | Cross-layer gap | P2 | FR-027/033 | Partially implemented / UI only / local state | E-17,E-23; B-051 |
| [FE-027](#fe-027) Administration: staff/facility lifecycle dependency | Backend gap | P2, blocked; access-policy resolution itself P0 | FR-029/033; U administrator; task staff accounts | Documented only / Missing | E-03/05/23; B-006/007 |
| [FE-028](#fe-028) Administration: audit/retention/governed settings | Backend contract gap | P2 UI, blocked; retention backend prerequisite P0 | FR-029/030/031/032/033; NFR-009/010 | Documented only reads/config/retention; partial internal knowledge / Missing | E-12/19/21/23; B-022/035/056/058/062 |
| [FE-029](#fe-029) Quality: shared truthful states, access/errors/a11y/design | Frontend gap | P0 — safety/access failure states must precede all workflows | FR-010/020/023; NFR-002/003/005/007/008; task conventions | Implemented and verified errors; UX evidence Unverified / Partially implemented | E-21/23; B-059/F-002 |
| [FE-030](#fe-030) Overview: permission-aware next actions | Frontend enhancement | P2 | U workflow; recommendation, not a PRD metric mandate | Unverified dashboard aggregate / UI only / local state | E-14/18/23; F-003 |
| [FE-031](#fe-031) Accessibility: optional permitted-content read-aloud | Frontend enhancement | P3, product/policy approval required | NFR-007; recommendation | Implemented and verified TTS / Missing | E-22,E-23; B-060 |

<a id="audit-section-11"></a>

## 11. Patient intake and report upload requirements

### Exact terminology and supported fields

Use “synthetic subject” and “case” until DEC-01 establishes patient-facing naming. `CreateCaseRequest` has only synthetic_subject_id, optional facility_id, consent_id. `CaseORM` stores subject UUID, facility UUID, state, version, opened_by and assigned_to; there is no patient model, patient_name, age, sex, date of birth, address, telephone, MRN, department or clinical priority in the case contract. `UserORM.display_name/email/password_hash` describe authenticated identities. Do not convert that user schema into a patient demographic form.

The user’s **patient name/intake request is a confirmed cross-layer requirement**: the PRD FR-007 also requires candidate demographic extraction, but it does not make a patient-name field mandatory in case creation. A permitted synthetic display name is a proposed product/schema addition pending DEC-01/BG-001; its requiredness, identity matching and relationship to account subjects remain unresolved. Demographic candidates from sample reports are distinct from authoritative intake identity.

Encounter fields are exact: encounter_type (1–100 chars), occurred_at (datetime), optional notes (≤2000 chars). Verbatim patient-provided narrative belongs to immutable text evidence (≤20000 chars), not a fabricated patient history. source_language is optional in text registration; encounter_id is optional but, if supplied, must belong to the case.

### End-to-end source trace and current breakpoints

| Step | Source behavior | Frontend need / blocker |
|---|---|---|
| 1. Identify permitted subject | Arbitrary UUID case field; consent FK requires existing user subject; tests seed users | FE-003; BG-001 subject creation/lookup/name/data class. No public end-to-end provisioning |
| 2. Explain use and capture DP consent | A04 request then A05 capture; exact purpose/notice; no disclosure record/read API | FE-006; BG-003. Checkbox cannot stand in for active purpose-bound consent |
| 3. Create case | A07 returns CREATED, not automatically CONSENTED | FE-003/004. Confirm lifecycle semantics; no unrestricted state editor |
| 4. Create encounter | A11 requires current DP consent; A12 lists | FE-005. Keep case/encounter persistent route context |
| 5. Record narrative | A13 stores verbatim text; intended READY; CONSENTED case may advance INPUT_RECEIVED | FE-007; TEXT response/language mismatch BG-005. No later correction/version read contract |
| 6. Upload sample report/form/image/audio | A14 existing case + DP consent + modality + optional encounter + one file; hashes/MIME/size/storage | FE-008. Separate evidence record per file; repeated requests, no bulk atomic API. Files do not themselves trigger the text branch’s case transition |
| 7. Scan readiness | Main binds NoOpScanner, returns PENDING; stored file remains STORED | BG-004. FE-008 shows “Stored; awaiting scan”, no fake processing/completion or force-ready action |
| 8. Run OCR/STT/language/extraction | A17/A18 require READY, current DP, processing:write and exact upstream run | FE-011/012/013; BG-006 identifiers/result reads. Formats allowed for upload are not equivalent to supported OCR/STT formats |
| 9. Evaluate timeline/gaps/conflicts | A20 requires ExtractionRun ID; latest successful reads A21–25 | FE-014/015; unavailable public extraction mapping BG-006; broader conflicts/correction BG-007 |
| 10. Prepare advisory/review | AI consent, retrieval→draft; case REVIEW_PENDING→queue→assignment→start→workspace | FE-017–022. Reviewer workspace can read original text and selected derived artifacts; cannot serve unassigned intake staff |
| 11. Correct/clarify/reapprove | No field verification API or registered clarification lifecycle; approved evidence writes rejected | BG-008/009/010. Cannot solve with local-only correction state |

**Trace conclusion:** identity→consent→case→encounter→narrative/upload→derived artifacts→review was traced end to end in source. It was **not executed**, and its public path is **not operationally complete**. Principal breaks are subject provisioning, disclosure/read consent, TEXT enum inconsistency, scan completion, derived-run discovery and reviewer correction/reapproval. Detailed screen/flow acceptance follows FE-003–015/019–022. A guided workflow with shared case context is appropriate; separate demographic pages are not justified by current contracts.

<a id="audit-section-12"></a>

## 12. Hospital/facility administration and staff-management findings

| Concern | Evidence-backed finding | Status / implication |
|---|---|---|
| Facility/hospital entity | Nullable facility UUID on CaseORM/UserRoleORM; no facility table, FK, CRUD or directory | Partially implemented scoping only; full facility administration Documented only (FR-033 Should) |
| Staff accounts | UserORM has individual email/password hash/display name/active/verified flags | Generic credentials exist; no normal provisioning UI/API |
| Create/invite/activate/disable staff | No registered endpoint/service workflow for these operations | Unsupported operational contract; BG-015. No frontend-managed passwords, flags or roles |
| First admin | FirstAdminBootstrapService + `scripts/bootstrap_admin.py` production-only, explicit system-wide scope, locked single bootstrap, atomic audit | Implemented and verified CLI boundary; cannot be reused to create later staff |
| Development credential provisioning | `scripts/seed_dev_admin.py` uses masked DSN; STARTUP §16 documents limitation | Not a reliable general onboarding path; not executed/worked around |
| Roles/permissions | Seven roles, 26 permission definitions, additive migration grants | RBAC implemented, not account creation. Actual DB mappings not queried |
| Role/facility assignment | UserRoleORM PK(user_id,role_id), one nullable facility value per role | No multi-facility same-role membership model/management API; scope selector unavailable in `/auth/me` |
| Reviewer eligibility | Active review:write + facility policy; assign/reassign commands exist | Selection API/directory and clinical qualification decision absent. User/role names alone do not prove qualification |
| Staff directory/details | No list/detail endpoint | Backend contract required; cannot populate reviewer/staff picker from verified source |
| Department/unit | No model/schema/contract discovered; not mandated as prototype expansion | Unsupported, defer unless DEC-04 explicitly requires minimal model |
| Recipient config | Active recipient read list; config JSON internal, no facility association/CRUD | FE-026 read selector possible; administration blocked BG-016 |
| Languages/required fields/workflow settings | Runtime Settings plus demo checklist JSON; no facility-backed settings/read/write governance | FR-033 Should, NFR-010; BG-019. Do not put secrets/provider credentials in browser |
| Retention/audit viewing | Append-only audit writes; no view permission/API; no retention policy/job/report | BG-017/018; separate backend controls from admin UI |
| Clinical/security/AI administration | Admin has all seeded permissions after 0015, no dedicated clinical-governance role | DEC-02/09 must define authority; no unrestricted hospital management system |

Hospital administrator staff creation, individual credential provisioning and facility configuration are **not genuinely supported as operational backend workflows** in this checkout. Existing per-user passwords and role assignment records are foundations. FE-027 remains a blocked dependency specification; prototype administration scope must be agreed before new account/configuration contracts. Facility analytics/workforce forecasting remain deferred.

<a id="audit-section-13"></a>

## 13. Role and permission capability matrix

These are **migration-derived grants**, not a read of production user assignments. Migrations are additive: earlier `0003/0004/0005` grant reviewer case/evidence/processing writes in addition to `0015`’s reviewer list. Ignoring those earlier grants would incorrectly report reviewer as read-only intake.

Permission sets (exact codes; `:read/write` below expands to two permissions):

- **ALL (26):** manage:users, manage:system, consent:read, consent:write, case:read, case:write, evidence:read, evidence:write, processing:read, processing:write, structuring:read, structuring:write, knowledge:read, knowledge:write, ai:read, ai:write, review:read, review:write, review:assign, escalation:read, escalation:write, referral:read, referral:write, handoff:read, handoff:write, recipient:manage.
- **D (23):** ALL minus manage:users, manage:system, recipient:manage.
- **N (11):** consent:read/write, case:read/write, evidence:read/write, processing:read, structuring:read, review:read/write, knowledge:read.
- **H (9):** consent:read/write, case:read/write, evidence:read/write, processing:read, structuring:read, review:write.
- **R (12):** case:read/write, evidence:read/write, processing:read/write, structuring:read, ai:read, review:read/write, escalation:read/write.

| Role | Verified permissions | Allowed workflows under source checks | Relevant frontend modules | Missing UI | Backend limitation |
|---|---|---|---|---|---|
| patient | No migration role_permission grant found | Login/profile/logout/TTS if active user provisioned; no self-triage permission | Login only by default | Session UX | No subject ownership/self-service flow; patient role is not authorization to process patient records |
| health_worker | H | DP consent/case/encounter/evidence intake, read processing/structuring; review write if assigned | Intake/cases/evidence; case-specific review only if eligibility approved | FE-003–015/020 | No review:read, so queue/workspace blocked despite review:write; no assign/escalation/processing write; qualification unresolved |
| nurse | N | Intake; read processing/structuring/knowledge; queue/workspace and review write when assigned | Cases/evidence/intelligence reads/review | FE-003–020 | Cannot trigger processing/structuring/AI or assign/escalate; qualification unresolved |
| doctor | D | Intake, processing/evaluation/retrieval/AI, queue assignment/review, escalation/referral/handoff; internal knowledge writes | All seven clinical nav areas subject to state/consent | FE-001–026/029 | No directory/source-admin API; recipient configure/ack another sender requires extra recipient:manage grant; qualifications not modeled |
| medical_officer | D | Same checked permissions as doctor, not a separate invented workflow | Same as doctor | Same | No department/title-specific policy differences verified |
| reviewer | R including historical writes | Case/encounter writes subject to consent, evidence/processing writes; structuring/AI reads; assigned queue review/escalation | Cases/evidence/review/escalations; selected intelligence reads | FE-004–023 | No consent:write, structuring:write, knowledge:read, ai:write, review:assign, referral/handoff. Cannot provision/assign itself or operate referral |
| admin | ALL | All permission checks technically grant; explicit scope still required | Admin modules plus clinical areas only if DEC-02 resolves authority | FE-002/027/028 | Current seed gives clinical privileges; technical administration alone must not qualify clinician |
| Intake operator (documented function, not new role) | Mapped to health_worker/nurse only after authority decision | Assisted synthetic intake, no invented extra powers | Guided intake | FE-003–010 | No separate role string or competence record |
| Qualified reviewer (documented function) | No qualification-specific permission/entity | Mapping requires DEC-02; review:write is actual current approval permission | Review workspace | FE-018–022 | No distinction field-verification vs final clinical approval privilege |
| Referral recipient (documented actor) | No dedicated role/account/callback permission | Sender/recipient manager manually records reference | Handoff | FE-025 | No recipient login, receiving/rejecting portal or authenticated recipient attestation |
| Facility/technical/clinical governance administrator (documented functions) | No dedicated role separation | Minimal scope to be approved DEC-02/04/09 | Blocked administration | FE-027/028 | Generic admin cannot imply multiple approved governance personas |

Visibility rules must use permission codes, not hardcoded role names. Cases/evidence need matching read permission; create/upload/write controls need their own permission plus consent/state. Structuring results require structuring:read; retrieval requires knowledge:read and AI consent; generation requires ai:write; queue/workspace review:read plus assignment; write review:write; assignment review:assign; escalation escalation:write; package referral:write; recipient list handoff:read; handoff actions handoff:write, referral consent and sender/manager constraints for ack/complete. `/auth/me` does not expose facility scope or assignment; do not infer either from a role label. No verified audit-view permission exists.

Hiding/disabling UI is UX only. Servers must enforce every object/action independently, including direct URLs and stale sessions. Current policy checks unioned permissions and facility access across roles independently; it does not prove that the role granting a permission is the same role granting the facility scope. Unscoped cases and subjects/consents require explicit DEC-03, not a client-side security workaround.

<a id="audit-section-14"></a>

## 14. Proposed frontend information architecture

Preserve the root login experience and existing clinical shell conventions. Keep case/encounter context in route hierarchy and cross-module links; do not make ordinary staff copy UUIDs between standalone tools. Existing module roots can become context pickers or indexes only when corresponding list/read contracts exist. No backend endpoint is implied by a proposed frontend route.

| Path | Purpose / intended permission-bearing user | Parent navigation | Requirements | Backend dependency | Existing or proposed |
|---|---|---|---|---|---|
| `/` → `/login` | Login-first entry, all users | Public auth | FE-001 | A01–03 | Existing; retain |
| `/login` | Individual credential sign-in | Public auth | FE-001 | Session storage/policy DEC-11 | Existing; revise |
| `/login/forgot-password` | Accurate unavailable/support recovery boundary | Auth | FE-001 | BG-021 if enabled | Existing; revise |
| `/dashboard` | Allowed next actions and verified workload only | Overview | FE-030 | A31/A30 as individually authorized; aggregate missing | Existing; revise |
| `/cases` | Scoped list or clearly limited exact-ID lookup | Cases | FE-004 | BG-002; A08 | Existing; revise |
| `/cases/new` | Guided subject/disclosure/consent/case step | Cases | FE-003/006 | BG-001/003; A04/05/07 | Existing; revise |
| `/cases/[id]` | Case header, state/history, workflow links | Cases | FE-004 | A08/A10/A12 | Existing; revise |
| `/cases/[id]/intake` | Narrative and encounter selection/create | Case subnav | FE-005/007/022 | A11–13; BG-005/008 | Proposed |
| `/cases/[id]/consent` | Purpose notices/status/withdrawal | Case subnav | FE-006 | A04–06; BG-003 | Proposed |
| `/cases/[id]/encounters/[encounterId]` | Interaction detail from case encounter list | Case subnav | FE-005 | A12, no standalone GET assumed | Proposed; may be side panel instead |
| `/cases/[id]/evidence` | Evidence list/upload/text/processing | Evidence, case subnav | FE-008/009/011/012 | A13–19/A29/30; BG-004–006 | Proposed |
| `/cases/[id]/evidence/[evidenceId]` | Original/derived/provenance inspector | Evidence | FE-010/013 | A15/A16; BG-005/007 | Proposed; panel acceptable |
| `/cases/[id]/intelligence` | Timeline/conflicts/checklist/retrieval/advisory | Clinical Intelligence | FE-014–017 | A20–28; BG-006/007/019 | Proposed |
| `/review` | Authorized review queue and filters | Review Workspace | FE-018 | A31; BG-022 | Existing; revise |
| `/review/[caseId]` | Assigned source-linked review/actions/versions | Review Workspace | FE-019–022 | A35–40; BG-005/008–011 | Proposed |
| `/cases/[id]/escalation` | Create/view/resolve known escalation | Escalations, case link | FE-023 | A41/A42/A36; BG-012 | Proposed |
| `/escalations` | Case selection or escalation index once readable | Escalations | FE-023 | BG-012 listing | Existing; revise conditionally |
| `/cases/[id]/referral` | Approved package/evidence/recipient selection | Referral & Handoff | FE-024/026 | A43–45/A49; BG-013/016 | Proposed |
| `/handoff` | Owned handoff index, not raw-command console | Referral & Handoff | FE-025 | BG-014 list/read | Existing; revise conditionally |
| `/handoff/[handoffId]` | Delivery/ack/closure/history/followup | Referral & Handoff | FE-025 | A46–48; BG-014 detail/version | Proposed |
| `/handoff/recipients` | Active recipient directory/conditional config | Referral & Handoff | FE-026 | A49; BG-016 CRUD/scope | Proposed |
| `/admin/staff`, `/admin/staff/[userId]` | Minimal approved staff lifecycle | Administration | FE-027 | BG-015, DEC-02/04 | Proposed, blocked |
| `/admin/facility` | Minimal approved facility settings | Administration | FE-027/028 | BG-015/019, DEC-04/09 | Proposed, blocked |
| `/admin/audit` | Read-only authorized audit | Administration | FE-028 | BG-017, new permission decision | Proposed, blocked |
| `/admin/retention`, `/admin/settings` | Approved lifecycle/configuration display | Administration | FE-028 | BG-018/019, DEC-09/10 | Proposed, blocked |
| `/evidence`, `/intelligence` | Context selection/redirect to authorized case module | Existing clinical roots | FE-009/014 | BG-002 or exact case lookup only | Existing; revise |
| `/design-system` | Internal component reference with no patient/account workflow | Developer reference; no clinical nav | FE-029 | No business API | Existing; retain development purpose |

Shared components: authenticated shell boundary; permission/action gate; case/encounter header and selector; consent notice/status panel; evidence inventory/uploader/preview/source locator; run/task status timeline; uncertainty badges; retrieval citation panel; advisory/human-content panels; reviewer assignment chooser; version/conflict confirmation; handoff status/history; common loading/empty/error/access states. Reuse existing primitives and palette. Do not create parallel incompatible status systems.

Workflow navigation: login→allowed dashboard/cases→subject/consent/case→encounter/narrative/evidence→verified processing outputs→intelligence/advisory→queue/assignment→review→approved referral→send/ack/complete. Manual escalation remains a separate human action once BG-012 supplies early-stage support. Back/refresh must recover case context from server-readable IDs; never synthesize successful records from local navigation.

<a id="audit-section-15"></a>

## 15. Detailed UI, workflow, API-contract, and acceptance requirements

### 15.1 Shared requirements inherited by every FE item

**S1 — truthful states.** Distinguish not selected, not requested, loading, completed empty, disconnected/contract unavailable, permission denied, consent required, validation failure, processing/provider failure, stale conflict and success. “No missing information/conflicts” is allowed only for a successful evaluated response, never for a disconnected panel. SUCCEEDED task, COMPLETED run, ACCEPTED validator and APPROVED human review remain separate badges. No invented percent progress, clinical urgency, negative finding or supported-language claim.

**S2 — fields/actions.** Use exact UUID/enum/length/integer rules from section 6; do not parse fractional versions with parseInt. Read expected versions from persisted responses, not editable default1 fields. Show IDs as secondary identifiers when no verified display-name contract exists. Do not add demographic requiredness or server-side fields. Search/sort/pagination must state whether server-supported or limited to loaded results. Confirm irreversible/transmitting/approval actions with actual case, version and purpose context.

**S3 — error/recovery.** Map actual envelope and correlation ID to safe messages; do not show raw request, patient narrative, tokens or provider exception bodies. Retain unsent edits in the current view without silently submitting after access/consent changes. Reload/reconcile on 409; distinguish unavailable/masked404 from permission403. If an operation outcome is uncertain, recover by a verified read/idempotency contract before offering repetition. No retry/cancel/delete button without a supported command and policy.

**S4 — accessibility/responsiveness.** Preserve Next App Router, React/TypeScript, Tailwind v4, existing shadcn/Base UI and Lucide conventions, pnpm only, Times New Roman including IDs/JSON, clinical navy/teal palette. At narrow widths use stacked sections, scrolling tables and toggleable source/detail panels; keep evidence→claim association. Label every control, associate errors with aria-invalid/aria-describedby, announce status through suitable live regions, provide keyboard file selection, accessible table captions/headers and textual statuses. Dialogs trap/restore focus; closed mobile drawer is not focusable/modal. Target PRD WCAG2.2 AA, without claiming it achieved before browser tests.

**S5 — test scope and durability.** Each future requirement needs observable UI tests for normal input, malformed input, permission/consent denial, empty/loading/error states, refresh/deep-link and optimistic conflict as applicable. Tests must use approved permitted fixtures when later authorized; none created now. Local UI acceptance before integration can verify inputs/layout/disabled states but cannot satisfy persistence/audit/provider acceptance. Phase 10 must verify actual server state/audit with safe approved test infrastructure. No localStorage patient/session scheme is prescribed before DEC-11.

Every detail below specifies user, permissions, preconditions, route/navigation, UI/flow, verified API and blocked contracts, acceptance and dependencies. Metadata and source IDs are in section 10. “Backend contract required” never names an invented endpoint.

<a id="fe-001"></a>

### FE-001 — Login, session and logout

**User/preconditions:** provisioned active user; login needs credentials, protected views need a current persisted session. **Route/navigation:** existing `/`→`/login`, auth recovery page and shell account menu. **UI:** retain email/password/visibility controls; generic invalid-credential message, submitting state, expired/revoked-session notice, profile ID/roles/permissions and functional logout. Do not display unreturned name/email as authenticated profile. Recovery page must say recovery is unavailable until BG-021 is implemented; no “email sent” outcome.

**Flow:** reach root login; validate email/nonempty password; future integration obtains A01 token and A03 current profile; enter only permitted shell routes after verification; expiry/revocation returns to login with no patient content; logout A02 revokes session and clears client session material. No hardcoded token, fake session, auto-dashboard bypass or fabricated remember-me/refresh flow.

**Contract:** LoginRequest(email,password)→TokenResponse; UserProfileResponse(id,is_active,roles,permissions); logout204. Bearer session is actual transport. Browser storage/cookie/server boundary requires DEC-11; refresh/password reset have no API. **Acceptance:** Given root visit, login appears first; invalid inputs make no successful-login claim; invalid/expired token blocks protected data; logout prevents future use of revoked session; recovery cannot report mail delivery; refresh revalidates session before protected render. **Dependencies/tests:** FE-002/029, DEC-11, BG-021 only for optional recovery; auth integration/access tests in Phase 10, no invented expiration policy beyond server token.

<a id="fe-002"></a>

### FE-002 — Permission-aware shell, routes and actions

**User/preconditions:** active profile A03; approved role/qualification/facility policy. **Route/navigation:** existing shell and every protected route. **UI:** filter seven clinical nav items by §13 permissions; show eligible action with specific state/consent requirement; access-denied route state; assignment indicator where returned. Block admin/staff/audit navigation until actual contracts and permissions exist. No facility switcher populated by assumed hospitals.

**Flow:** resolve session/profile; calculate visibility per actual permission; load requested object under server authorization; expose operation only when returned state, consent and ownership permit; on403/404 stop data display and offer allowed navigation. Qualification is a backend/policy condition, not a role-name heuristic. Health_worker’s review:write without review:read must be surfaced as an unresolved workflow permission mismatch.

**Contract:** A03 omits role_facilities; object scope is server-enforced. **Backend contract required:** BG-020 scope/action eligibility/profile metadata, DEC-02/03. **Acceptance:** A user lacking processing:write sees no execute action even with processing:read; no forbidden route renders cached clinical data; direct URLs remain denied by server; current admin grants are described accurately but never asserted clinically qualified; multiple-role scope cannot be resolved by client union guesses. **Dependencies/tests:** FE-001/029, BG-020; role/permission/object-scope matrix tests including changed permissions between load and submit. P0 because dependent pages cannot infer safe access.

<a id="fe-003"></a>

### FE-003 — Subject identification and case creation

**User/preconditions:** case:write, approved subject identity/data-class model, active matching DP consent; chosen facility only if authorized. **Route/navigation:** `/cases/new`, Cases. **UI:** guided sections permitted-data disclosure→subject→consent→case summary. Existing supported fields are synthetic_subject_id UUID, optional facility_id UUID, consent_id UUID. Replace title/MRN/mandatory priority/checkbox payload with contract-backed selection. Synthetic patient display name is a **proposed addition pending DEC-01/BG-001**; requiredness and demographic fields not decided. Show urgency “Unassigned — qualified review required” as PRD disclosure, not a payload field.

**Flow:** identify provisioned permitted subject through future lookup; capture FE-006 consent; summarize exact subject/facility/notice; submit A07; navigate returned case ID, showing CREATED and real version. Do not invent clinical lifecycle progress from success. No independent patient account creation in browser.

**Contract:** CreateCaseRequest→CaseResponse; DP exact subject/notice1.0 and scoped case:write. **Backend contract required:** identity lookup/provisioning/name/data classification; facility discovery; safe CREATED→CONSENTED orchestration BG-001/011. **Acceptance:** malformed UUID is rejected locally; active consent for another subject/withdrawn purpose cannot create case; optional facility stays optional; no urgency sent; success route uses returned ID; refresh recovers persisted case; unavailable identity contract visibly blocks intake completion. **Dependencies/tests:** FE-001/002/006/004, BG-001/003/015, DEC-01/03/05; identity/consent/scoped creation and stale-consent tests.

<a id="fe-004"></a>

### FE-004 — Case discovery, details and history

**User/preconditions:** case:read; case:write only for permitted nonclinical operations. **Route/navigation:** `/cases`, existing `/cases/[id]`, Cases. **UI:** case ID, synthetic subject ID, optional facility, actual state/version, opened_by/assigned_to, created/updated timestamps; workflow links and actual state history actor/time/from/to/reason/version. Table uses those fields rather than unsupported title/MRN/priority. Exact-ID lookup can use A08 while list is unavailable; label limitation. Future list/filter/sort/page controls require BG-002 (filters/order/page contract unresolved).

**Flow:** choose a readable case or enter exact UUID; bind dynamic route params; load A08/A10/A12; link encounters, consent/evidence/intelligence/review/referral using same case; reload on state changes; preserve 404 masking. Do not offer arbitrary state-dropdown transitions into REVIEWED/REFERRED/COMPLETED.

**Contract:** CaseResponse/CaseHistoryResponse/EncounterListResponse. A09 exists but lacks specialized invariants; only product-approved safe lifecycle commands may replace it. **Backend contract required:** scoped list/search, assignment/readability semantics, safe lifecycle BG-002/011. **Acceptance:** two distinct URLs request distinct cases; no fixed Under Review label; denied/notfound case yields no previous-case data; history reflects server versions; absent assigned_to stays unassigned; no working filter/page promise before contract. **Dependencies/tests:** FE-002/003/005/029, BG-002/011; params/navigation/404/history/concurrency tests.

<a id="fe-005"></a>

### FE-005 — Encounter creation and intake context

**User/preconditions:** case:write plus active DP for creation; case:read for list; readable case. **Route/navigation:** proposed case intake page and encounter side panel/detail, Cases subnav. **UI:** encounter list columns ID, type, occurred_at, optional notes; create dialog type required1–100, datetime required, optional notes≤2000. Show input timezone conversion explicitly; no invented visit taxonomy or mandatory encounter for evidence.

**Flow:** open case; list A12; choose existing encounter or create A11; retain returned encounter in narrative/upload context; verify optional selection belongs to case; show detail from A12 record without assuming standalone encounter GET. No encounter editing action without contract.

**Contract:** CreateEncounterRequest→EncounterResponse; list returns case_id/encounters; EncounterService checks facility and DP. **Acceptance:** invalid/missing datetime/type or notes over2000 blocks submission; denial/withdrawn consent preserves unsent input; encounter from another case is not selectable and server rejects tampering; omitted encounter yields case-level evidence, not an invented encounter; refresh recovers created encounter; occurred_at remains an encounter anchor, not a report date. **Dependencies/tests:** FE-004/006/007/008/029, DEC-01 timezone conventions; create/list/association and timezone display tests. No demographic fields inferred from encounter notes.

<a id="fe-006"></a>

### FE-006 — Purpose-specific consent and prototype disclosure

**User/preconditions:** consent:write; authorized subject-management policy BG-003; existing subject. **Route/navigation:** case creation disclosure and proposed `/cases/[id]/consent`, case subnav. **UI:** approved advisory/non-diagnostic/qualified-review/synthetic-sample disclosure; purpose panels DP, AI, referral with exact notice version, state and available acknowledgement/withdrawal. `export` remains unsupported until approved workflow. Show actor/time only when returned by future contract; current ConsentResponse does not supply them. No blanket consent checkbox.

**Flow:** display approved notice before intake; request A04 with subject/purpose/notice; explicit acknowledgement captures A05; dependent actions use active exact consent; confirm A06 withdrawal, explain policy-approved processing/access consequences; stop dependent actions after withdrawal. Do not claim withdrawal deletes data.

**Contract:** ConsentRequest(subject_id,purpose,notice_version)→ConsentResponse; REQUESTED→ACTIVE→WITHDRAWN. **Backend contract required:** read/list/events/disclosure/data-class audit, scoped subject management, reconsent/duplicate behavior and safe missing-ID error BG-003. Arbitrary strings in schema do not authorize arbitrary purposes. **Acceptance:** unrelated-subject consent cannot authorize intake; no intake/AI/referral without corresponding active purpose; existing consent reload is accurate or explicitly unavailable; notice acknowledgement persists approved record; withdrawal never reports deletion; unexpected500 is safe/correlated, not mislabeled successful withdrawal. **Dependencies/tests:** FE-003/007/008/017/024/029, BG-001/003, DEC-01/03; purpose/version/mismatch/access/withdrawal tests.

<a id="fe-007"></a>

### FE-007 — Verbatim narrative intake

**User/preconditions:** evidence:write, current DP, case accepts evidence, optional same-case encounter. **Route/navigation:** case intake page, accessible from case header/evidence workspace. **UI:** original narrative textarea≤20000, character count, optional source_language, encounter selection, subject/case/consent context, submit confirmation; original text display after saved read. Empty narrative behavior needs product clarification because schema has no min_length; do not label a new min as verified backend rule.

**Flow:** choose case/encounter; read prototype disclosure; enter verbatim account; register A13; use returned evidence ID/state; link original/candidate views; later corrections must become attributed versions/new evidence under approved policy, not mutate original locally.

**Contract:** RegisterTextRequest/EvidenceResponse; EvidenceService stores text and audit, auto-advances only CONSENTED case. **Backend contract required:** fix uppercase modality, intake raw-content read and correction/version linkage BG-005/009. No client lowercase coercion can fix the server response failure. **Acceptance:** original wording/Unicode/numbers stay unchanged; >20000 locally rejected; wrong/withdrawn consent and postapproval writes are denied; failed save never displays persisted success; refresh retrieves saved original after read contract exists; normalized content is visibly separate. **Dependencies/tests:** FE-003–006/009/013/029, BG-005/009, DEC-06; public text response and exact-text persistence tests after backend correction.

<a id="fe-008"></a>

### FE-008 — Report/form/image/audio upload

**User/preconditions:** evidence:write, existing readable case, active DP, optional same-case encounter; permitted sample file. **Route/navigation:** case evidence workspace upload section, Evidence and intake links. **UI:** case/encounter header, prototype restrictions, one-file picker with keyboard control, modality selector using actual lowercase enum, filename/bytes/MIME summary and effective approved allowlist/max size; default values labeled defaults until configuration confirmed. Per-file result panel with evidence ID/state, validation recovery and no ready/processed claim from upload success. No unsupported report-date/department/patient-demographic metadata fields.

**Flow:** enter from case; choose optional encounter and report/form/document, basic image or sample audio modality; select one file; check configured extension/size; submit multipart A14; display actual returned STORED/READY/QUARANTINED; later find record through FE-009; repeat separate requests for multiple reports without claiming atomic batch. Scan-pending blocks processing/download. Cancellation only abandons unsent local file, not a nonexistent server cancel.

**Contract:** case_id,consent_id,modality,file,optional encounter_id→EvidenceResponse; server enforces magic/declared/extension consistency, checksum duplicate, size/nonempty and scope. **Acceptance:** unsupported/empty/oversize file yields explicit failure; MIME rejection differs from duplicate409/storage503; pending scan stays STORED; no diagnostic-image interpretation claim; lost response is reconciled before blind reupload; accepted evidence persists after refresh once BG-005 read is supplied. **Dependencies/tests:** FE-004–006/009–012/029, BG-004/005, DEC-06/07; upload rejection, association, scanner pending/rejected, duplicate and storage-recovery tests.

<a id="fe-009"></a>

### FE-009 — Case evidence inventory and metadata

**User/preconditions:** evidence:read; evidence:write only for intake actions. **Route/navigation:** proposed `/cases/[id]/evidence`, existing `/evidence` as case context entry. **UI:** rows ID, filename or “text evidence”, modality, encounter, MIME, size, source_language if returned, state, creator/time; metadata panel displays exactly 12 public fields including provenance, not internal storage keys/SHA unless contract deliberately added. Actions view, upload/narrative, permitted processing and download; delete remains blocked.

**Flow:** load case inventory from future scoped list contract; choose row; A15 metadata; route/panel retains evidence/case/encounter; link source and runs; refresh update state. Review workspace is an additional assigned-review reader, not an intake list workaround. Optional local filters on loaded modality/state must state loaded scope; pagination only if server implemented.

**Contract:** A15 exists; `EvidenceListResponse` and service list_for_case exist but are not registered. **Backend contract required:** list/raw content/derived read BG-005, no invented GET path. **Acceptance:** disconnected/permission/no-evidence states distinct; selection never mixes two cases; state is server value; accepted file later remains discoverable; failed list cannot imply no evidence; deletion badge enum alone does not enable delete. **Dependencies/tests:** FE-004/008/010–013/029; BG-005/018; list/detail/deep-link/refresh/permission tests.

<a id="fe-010"></a>

### FE-010 — Original source inspector and exact provenance

**User/preconditions:** evidence:read and ready stored file; assigned review access separately for A36. **Route/navigation:** evidence detail/source side panel, linked from timeline, candidates, retrieval and review assertions. **UI:** original file viewer where browser/provider supports it, safe download fallback, page/region locator, text span highlight, table cell/context and audio interval replay. Only render locator dimensions/IDs actually returned; unavailable exact locator explicitly labeled. Timestamps from STT fallback must not masquerade as provider-measured intervals. Do not render report text/AI as executable HTML or scripts.

**Flow:** choose cited assertion/candidate; resolve same-case source; fetch A15 and A16 only on deliberate access; show original alongside derived text; use source-qualified page/span/interval; refresh expired SAS via verified action; preserve source when navigating back. Original text is readable through reviewer workspace today, not through file download without storage key.

**Contract:** SecureDownloadResponse URL/expiry; A36 region boxes/transcript timestamps/provenance subset. **Backend contract required:** complete locator/table/source resolver/raw text and read policy BG-005/007, DEC-03/07. **Acceptance:** missing source never opens unrelated evidence; nonREADY file remains unavailable; expired URL does not persist/share as permanent link; text originals unchanged; unknown interval/cell shows limitation; keyboard can switch assertion/source and operate audio; no secrets/URLs in logs. **Dependencies/tests:** FE-009/013/014/017/019/029, BG-004/005/007; source fidelity/expiry/isolation/unsupported preview tests.

<a id="fe-011"></a>

### FE-011 — Processing controls and run status

**User/preconditions:** processing:write, current DP, READY evidence, valid modality/upstream completed run; processing:read for read. **Route/navigation:** case evidence processing section, source detail. **UI:** four exact processor types; explain OCR versus STT versus normalization/extraction; upstream run picker and optional target_language only where supported. Show run_id, evidence_id, provider, config_version, status/start/end/failure from ProcessingRunResponse. Do not show structure_extraction or clinical_intelligence as processing types. Show scan readiness separately.

**Flow:** choose evidence; select valid processor/source; A17 synchronous response or A18 async request per agreed integration design; A18 result is task identity, route to FE-012; obtain actual ProcessingRun identity via BG-006; A19 reload run; expose artifacts via approved output reader. No automatic pipeline or state-transition button that assumes outbox notifications orchestrate every step.

**Contract:** TriggerProcessingRequest and exact source requirements §6. Invalid enum currently may return 500; report safely. **Backend contract required:** run/task/extraction discovery, output contracts, failed-run retry/idempotency BG-006. **Acceptance:** STORED cannot be processed; wrong/incomplete upstream run rejected; FAILED synchronous run is failure even with HTTP 200; refresh resumes actual run; source ID cannot be copied as ExtractionRun ID; failed idempotent run not represented as fresh retry. **Dependencies/tests:** FE-008–010/012/013/029, BG-004/006, DEC-06/07; per-processor source/modality/failure tests.

<a id="fe-012"></a>

### FE-012 — Task polling, durable outputs and recovery

**User/preconditions:** case:read for A29/A30; task case scope; operational retry authority unresolved. **Route/navigation:** case evidence processing/task panel, case activity links. **UI:** task table type/entity/status/timestamps/correlation/error; independent linked processing-run state; no percent progress or invented steps. Task detail shows PENDING/QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED values only when returned. Explain prolonged pending as unresolved dispatch, not success; cancellation command absent.

**Flow:** on A18 use returned `run_id` as task ID; poll A29/A30 under a bounded backoff policy approved during integration; stop when hidden/session denied; reload task list on refresh; follow future result identity to processing/extraction/draft; failure displays safe category and supported recovery. CLI replay/stale recovery remains operational, not a guessed browser action.

**Contract:** AsyncTaskResponse omits result_json/attempts/heartbeat; no websocket/SSE, retry or cancel contract. **Backend contract required:** BG-006 output identifiers/status reconciliation/retry eligibility and progress semantics; do not infer task result from entity_id alone. **Acceptance:** resumed URL recovers server status; no duplicate trigger on polling refresh; terminal worker failure remains FAILED and task success never implies clinical verification; access loss clears results; permanent failure stops polling and preserves safe recovery advice; no fake retry button. **Dependencies/tests:** FE-001/002/011/029, BG-006, DEC-12; task/run reconciliation, stale/retry/duplicate/outage tests.

<a id="fe-013"></a>

### FE-013 — Extraction, normalization and reviewer uncertainty

**User/preconditions:** processing:read or authorized assigned workspace; same-case persisted results; field correction requires future authorization contract. **Route/navigation:** evidence detail and intelligence/review field panel. **UI:** candidate table field_type, original value, normalized value, verification status, provenance and optional uncalibrated provider confidence labeled as such. OCR pages/reading order/table cells and transcript segments/speaker/language; original/translated/normalized views separate. Empty/unreadable/unverified/conflicting are distinct; demo outputs prominently limited to verified fever/ISO-date extraction, not full report demographics.

**Flow:** open completed run; read approved derived artifact contract; select candidate/source; compare original/normalized/translation; verify/correct/undo only once BG-009 supplies persisted attributed operations, never local badge toggles. Keep original intact and trigger downstream re-evaluation/reapproval under BG-010 policy.

**Contract:** ORM/repository artifacts exist; A36 omits normalized/confidence/language/tables/ExtractionRun ID. **Backend contract required:** BG-005/007/009 expanded result/correction/source contracts, DEC-06 provider quality. **Acceptance:** null confidence is unknown, not zero certainty; original number/unit never overwritten; unreadable field yields abstention; no generic patient name or laboratory extraction claim from demo; changes persist actor/reason/version after contract exists; source links exact and all conflicts preserved. **Dependencies/tests:** FE-010–012/014/019/021, BG-005/007/009/010; original/normalized/provenance/undo/outage tests.

<a id="fe-014"></a>

### FE-014 — Timeline and conflicting facts

**User/preconditions:** structuring:read/DP; structuring:write/DP for evaluation; exact same-case ExtractionRun. **Route/navigation:** case intelligence timeline/conflicts sections and reviewer links. **UI:** evaluation summary/run/extraction IDs; timeline source_statement/event_type/raw temporal expression/precision/resolution/normalized date bounds/unresolved reason/status with evidence/candidate links. Conflicts table field/status/detection run plus all candidates once link contract exists. Distinguish reported event date, document date, encounter date and inference when supported; never substitute uploaded_at as onset or silently order UNKNOWN entries.

**Flow:** select verified extraction result; A20 evaluate; reload A25 then A21/A22; show run status; inspect sources side by side; correction/resolution waits on persisted BG-007/009. Current onset-only, single-extraction behavior must be described accurately.

**Contract:** EvaluateRequest/EvaluateResponse/TimelineEventResponse/ConflictResponse; no candidate links in A22, no date-type/anchor completeness. **Backend contract required:** cross-evidence comparison/resolution/locator BG-007; ExtractionRun identity BG-006. **Acceptance:** failed/not-run is not “no conflict”; unresolved relative date stays unresolved; differing candidates remain visible; no clinical contradiction rule invented; refresh retains exact successful run provenance; other-case extraction denied. **Dependencies/tests:** FE-011/013/015/019/029, BG-006/007/009, DEC-06; date semantics/cross-case/conflicting-candidate tests.

<a id="fe-015"></a>

### FE-015 — Missing information and bounded follow-up display

**User/preconditions:** structuring:read/DP; completed or NO_INPUT persisted evaluation; approved checklist configuration. **Route/navigation:** case intelligence gap/question sections and reviewer workspace. **UI:** checklist_version/requirement_key/status/materiality/resolution; separate MISSING/CONFLICTING/UNREADABLE/UNVERIFIED/SATISFIED groups and links; question_text/round_number/status/generator_version/missing_item_id. “Not provided” never “absent symptom”. Current demo_v1 maximum 3 per round/2 rounds; PRD upper bound5 is not a requirement to generate five. Clinical question templates/demo severity text require approval before presentation as an approved workflow.

**Flow:** read A23/A24/A25; staff inspect suggested questions and evidence; future select/ask/answer/stop routes are FE-022/BG-008. Display unanswered unknowns without sending questions automatically or pretending second round/closure exists.

**Contract:** MissingInfoResponse/QuestionResponse; first-round generator only, no answer/stop. **Acceptance:** disconnected view says not evaluated; successful missing rows keep actual categories/checklist; generated count does not exceed approved configured bound; no automatic clinical finding from missing input; unanswered items survive refresh; no local question checkbox claimed persisted. **Dependencies/tests:** FE-013/014/019/022/029, BG-008/019, DEC-06/09; unknown/category/question-limit/empty-response tests.

<a id="fe-016"></a>

### FE-016 — Approved-knowledge retrieval and citations

**User/preconditions:** knowledge:read/AI, readable case, approved published corpus. **Route/navigation:** case intelligence retrieval and reviewer citations. **UI:** query 1–4000, corpus_version 1–100, HYBRID/DENSE/SPARSE, strict integer top_k1–50 (default 10); result status/hash/corpus/embedding/filter/count/zero reason/time; rank/source IDs/citation/available scores. Scores are search relevance, not clinical confidence. Corpus picker requires discovery contract; no guessed versions.

**Flow/API:** select approved corpus/query; A26 RetrievalRequest→RetrievalResponse; A27 reload exact case/run; inspect future approved source passage; carry retrieval_run_id to FE-017. Internal KnowledgeService does not create a public governance UI. **Backend contract required:** BG-019 source/corpus/passage reads, governance, top_k dedup decision. **Acceptance:** Given approved corpus, results retain pinned citation/version; wrong/unpublished sources are not offered; ZERO_RESULTS/FAILED/loading distinct; query/top_k limits enforced; refresh retains run; changed top_k does not falsely promise new results if dedup returns prior run; no patient evidence added to knowledge corpus. **Dependencies/tests:** FE-002/010/017/019/029, BG-019, DEC-09; corpus isolation, zero-result, citation and idempotency tests.

<a id="fe-017"></a>

### FE-017 — Advisory draft, safety and trace

**User/preconditions:** ai:write/AI for generation; exact same-case completed/zero-result retrieval; read today through assigned workspace. **Route/navigation:** case intelligence advisory section and review detail. **UI:** four exact task values; summary/claims/missing IDs/limitations, assertion status/source link, validator versus human badges; rejected output quarantined from authoritative display. Replace “verified AI advisory drafts” claim. Model/prompt/schema/retrieval/policy/case/note trace only from returned metadata.

**Flow/API:** choose retrieval/task; A28 ExecuteAdvisoryRequest→AIDraftResponse; inspect validation errors/provenance; show rejection/provider failure; link eligible draft to human review, never mutate urgency/disposition/referral from generation. **Backend contract required:** BG-019 durable draft read/version/trace; BG-011 generic clinical-transition invariants. Existing rejected-output review guard is implemented, not a missing contract. **Acceptance:** ACCEPTED is never labeled clinically verified; rejected/policy-blocked output remains nonreviewable through the existing server guard; no missing source guessed; failure gives safe recovery; refresh restores exact draft/version once reader exists; diagnosis/treatment not presented as authoritative output. **Dependencies/tests:** FE-010/015/016/018–021/029, BG-011/019; malformed/injection/provenance/policy/outage tests.

<a id="fe-018"></a>

### FE-018 — Queue, assignment and review start

**User/preconditions:** review:read for queue, review:write/AI for entry/start, review:assign/AI for assign/reassign; eligible active same-scope reviewer. **Route/navigation:** `/review` queue→proposed `/review/[caseId]`. **UI:** case/encounter/status/reviewer/technical priority_bucket/version columns; server status/assigned_to filters, refresh, case links. Assignment chooser uses future eligible staff directory; reassign reason 1–1000. No fictional names or manually defaulted versions. Clinical qualification DEC-02 remains necessary.

**Flow/API:** A31 list; A32 enter REVIEW_PENDING case; A33/A34 assign/reassign loaded queue version; A35 start; open FE-019. **Backend contract required:** BG-015 directory, BG-022 exposed pagination/count/order. Interim exact reviewer UUID is a proposed limited fallback, not staff management. **Acceptance:** lacking assign permission prevents assignment even on direct request; stale409 does not overwrite; filters survive back; no full queue count claimed beyond first 50; start shows returned IN_REVIEW; no automatic self-assignment; empty differs from access denial. **Dependencies/tests:** FE-002/004/017/019/029, BG-015/020/022, DEC-02; assignment/scope/stale/limit tests.

<a id="fe-019"></a>

### FE-019 — Connected reviewer workspace

**User/preconditions:** review:read/AI, existing queue, assigned reviewer or review:assign override; current case/queue/draft versions. **Route/navigation:** proposed review detail, linked case/intelligence. **UI:** case/encounter/owner header; original source panel; derived candidate/timeline/gap/conflict sections; separate AI advisory and human-edited content; policies/uncertainty, prior decisions/escalations/referral summaries. Deliberately type/render A36’s observed structure; do not use arbitrary JSON as clinical workspace. Narrow layout switches panels while preserving selected assertion/source.

**Flow/API:** authorize and load A36; inspect original and derived sources; fetch A15/16/A21–25 only if own permissions permit; read actual latest human edit before approving; actions reload authoritative content/version. **Backend contract required:** BG-005 complete sources/results, BG-010 edited-content/history, BG-019 trace. **Acceptance:** approved display is exact approved/sent human content; original and AI origins distinct; source unavailable explicit; denied URL clears previous-case content; refresh retrieves real versions; reviewer permission does not implicitly grant all extra read endpoints. **Dependencies/tests:** FE-010/013–018/020/021/029, BG-005/010/011; source fidelity/edited-content equality/assignment/deep-link tests.

<a id="fe-020"></a>

### FE-020 — Edit, reject, approve and disposition

**User/preconditions:** review:write/AI; assigned or approved override, IN_REVIEW; qualified authority DEC-02; current draft/queue/case versions and safe validator/policy gate. **Route/navigation:** review detail action panel. **UI:** structured human note editor after schema approved; separate neutral save/edit, accept, reject with rationale1–4000, final APPROVE/REFER/REJECT; confirmation identifies exact case/content/version. REQUEST_CLARIFICATION routes to future dedicated workflow, ESCALATE to FE-023. No viewing/inactivity approval.

**Flow/API:** inspect source; save neutral edit after BG-010 fixes semantics; reload content/version; A37 accept or A38 reject; A40 explicit disposition uses all three versions. REJECT needs rejected draft plus rationale; APPROVE/REFER need accepted draft. Current A39 immediately approves; validation/policy-rejected drafts already fail the DRAFT-only guard. **Neutral edit/reapproval and generic case-transition safety are blocked until BG-010/011.** Returning rejected draft is absent; never invent resubmit.

**Acceptance:** edit alone cannot approve; unsafe AI cannot become authoritative; stale version yields409/no overwrite; explicit qualified actor/reason/version audited; generic unsupported decision options unavailable; rejection reason persisted; clinical permission is server-enforced. **Dependencies/tests:** FE-018/019/021–023/029, BG-008/010/011/020, DEC-02; approval/reject/return/unsafe-draft/concurrency tests.

<a id="fe-021"></a>

### FE-021 — Versions, differences and reapproval

**User/preconditions:** authorized reviewer, approved material-change policy and persisted attributed content history. **Route/navigation:** review detail Versions tab/panel, case history link. **UI:** content origin/actor/time/reason/version list, approval/disposition linkage, adjacent diff (FR-022 Should), current approved versus edited status, material-change/reapproval warning. CaseStateHistory is not note history; raw AI content is not latest human edit.

**Flow/API:** future history read; compare; authorized correction/reopen; invalidate old approval, create attributed new draft, repeat FE-020; supersede affected referral under policy. DraftEditVersionORM exists, but no public read/sequence/approved-edit identity; evidence writes postapproval refused with no reopen. **Backend contract required:** BG-010 version/read/invalidation/reapproval; BG-019 trace; material-change meaning DEC-09, no invented thresholds.

**Acceptance:** material edit cannot retain approval; UI/preview/transmission reference same approved content/version; history survives refresh; contradictory sources remain separate; denied/stale edit does not overwrite; missing contract blocks reopen instead of SQL/generic-state bypass. **Dependencies/tests:** FE-013/019/020/024/029, BG-010/011/013/019; edit→invalidate→reapprove→package equality tests.

<a id="fe-022"></a>

### FE-022 — Manual fallback and clarification lifecycle

**User/preconditions:** approved intake/reviewer authority, persistent fallback/clarification contracts, qualified final human review. **Route/navigation:** intake clarification and review Manual note/Return panels. **UI:** PRD note sections concern/evidence/timeline/unresolved/source; actor/time/reason/version; suggested questions with staff selection, response/source, round/status/Stop. Missing remains unknown; no treatment/scoring additions.

**Flow/API:** AI outage→manual intake/evidence/note; future attributed note save/approval; choose questions within approved bound (PRD≤5/demo3); capture sourced answers, reevaluate; stop maximum 2 rounds or staff decision; owned return to review. A24 reads questions only; ClarificationService is unregistered and omits durable answer/round logic; ReviewerNoteORM creation is unused. **Backend contract required:** BG-008/009/010, DEC-02.

**Acceptance:** no AI outage lockout of authorized manual workflow/escalation; absent values never negatives; answer/stop/round persists after refresh; bounded rounds enforced server-side; returned case ownership/version explicit; local-only note never approved. **Dependencies/tests:** FE-005–007/015/019–021/023/029, BG-008/009/010/012; bounded clarification/manual outage/return/audit tests.

<a id="fe-023"></a>

### FE-023 — Manual escalation, ownership and resolution

**User/preconditions:** actual review action escalation:write/AI plus active queue/assignment and case/queue versions; early intake/outage requires BG-012/DEC-05. **Route/navigation:** case/review action, proposed case escalation detail; existing escalation root becomes readable index only with contract. **UI:** reason 1–4000, source/case/actor, OPEN/RESOLVED, resolver/notes 1–4000; owner/history/followup only if returned; no ACKNOWLEDGED button because enum has no command.

**Flow/API:** A41 create using loaded versions; reload ESCALATED; A42 authorized resolution returns REVIEW_PENDING/IN_REVIEW. Early independent escalation is visibly blocked today, not locally “completed”. **Backend contract required:** BG-012 early permission/ownership/read/history/ack; no urgency threshold invented. **Acceptance:** human action independent of model recommendation; no waiting for AI once bypass exists; stale409 no duplicate; wrong assignment/case denied; reason/actor auditable; refresh restores actual record; no resolution/acknowledgement shortcut. **Dependencies/tests:** FE-002/004/018–022/029, BG-012, DEC-02/05; intake/outage/review/stale/ownership tests.

<a id="fe-024"></a>

### FE-024 — Approved referral package

**User/preconditions:** referral:write/RF; REVIEWED current approve/refer decision and unchanged approved draft; selected same-case evidence. **Route/navigation:** proposed case referral, review/case links, Referral & Handoff. **UI:** actual approved note/decision/version preview; evidence selection1–100 deduped UUIDs; prepared_by/package version/status; finalize confirmation and readable superseded packages. Replace raw comma-separated IDs with record selection.

**Flow/API:** A43 prepare selected evidence; inspect exact persisted approved_reviewer_content; A44 finalize; FE-026 recipient→A45 initiate. Current response omits preview and finalize does not revalidate current approval. **Backend contract required:** BG-013 package read/preview/finalize/send revalidation; packaging unready/quarantined evidence policy DEC-07/08.

**Acceptance:** rejected/unreviewed/changed note never sendable; preview equals transmitted approved version; cross-case evidence denied; empty/>100 rejected; duplicate handling matches service; repeat finalize real status; refresh recovers package rather than rebuild local content. **Dependencies/tests:** FE-009/019–021/025/026/029, BG-005/010/013, DEC-08; package equality/supersession/current-approval tests.

<a id="fe-025"></a>

### FE-025 — Delivery, acknowledgement, closure and followup

**User/preconditions:** handoff:write/RF; finalized current package/active recipient; ack/complete sender or recipient:manage plus facility scope; current handoff/case versions. **Route/navigation:** handoff index/detail, case referral link. **UI:** case/package/recipient/channel/sender, status, returned sent/ack times, reference 1–500, failure and versions; stages DRAFT/READY/SENDING/SENT/ACKNOWLEDGED/COMPLETED separate. Additional receipt/reject/accept/owner/deadline conditional BG-014. Label simulated delivery; no live channel claim.

**Flow/API:** A45 initiate; confirm A46 send→queued READY; poll task/future handoff reader→actual SENT; authorized human A47 records real acknowledgment evidence; A48 explicitly completes with two versions; unacknowledged remains open. Recovery only supported retry; no hardcoded timeout. Worker discards actor and lacks fresh referral-consent check at delivery.

**Backend contract required:** BG-014 read/history/failure/followup/receipt/version/revalidation, BG-006 task result. **Acceptance:** queued≠sent≠acknowledged≠completed; no close before ack; unrelated writer denied; withdrawn consent blocks queued delivery after fix; failure/current version survives refresh; followup has configured accountable owner; no UI-generated recipient acknowledgment. **Dependencies/tests:** FE-012/020/024/026/029, BG-006/013/014, DEC-08; send/fail/withdraw/ack/close/idempotency tests.

<a id="fe-026"></a>

### FE-026 — Recipient selection and bounded management

**User/preconditions:** handoff:read for list; scoped config policy DEC-08; recipient:manage alone exposes no CRUD. **Route/navigation:** referral chooser/proposed recipient directory. **UI:** active id/name/type, selected-recipient confirmation; optional loaded-list search labeled local; no internal config_json/contact/credential/channel fields. Admin add/edit/disable blocked until contract.

**Flow/API:** A49 list→selected real recipient→A45; empty list blocks initiation; server rechecks active selection. **Backend contract required:** BG-016 facility scope/config/audit/management; current list global, no CRUD/detail/page contract. **Acceptance:** no fictional recipients; denied list hides records; refreshed selection remains only if valid; inactive/blank recipient denied; type does not imply supported channel; admin cannot locally save configuration. **Dependencies/tests:** FE-002/024/025/027/029, BG-016, DEC-08/09; empty/permission/inactive tests. P2 directory presentation supports P1 selection in referral.

<a id="fe-027"></a>

### FE-027 — Minimal staff/facility administration (blocked)

**User/preconditions:** DEC-02/04 authority; actual manage:users/manage:system definitions but missing scoped lifecycle. **Route/navigation:** proposed admin staff/detail/facility. **UI conditional on contract:** directory user ID/display_name/email/active/roles/facility, approved provisioning identity/role/scope and individual activation delivery. UserORM fields are internal evidence, not existing staff request. No shared credentials, hashes/plaintext passwords, unrestricted grants or invented departments.

**Flow/API:** future scoped directory; authorized create/invite; individual activate/credential mechanism; assign permitted role; disable/change scope with audited effect; use same eligible directory for reviewer assignment. First-admin CLI is not general provisioning. **Backend contract required:** BG-015 staff/facility CRUD/activation/deactivation/credentials/eligible directory and BG-020 role/scope/qualification.

**Acceptance:** no browser-created accounts/permissions; each real provisioning audited and cross-facility denied; disabling impacts sessions per approved backend policy; admin label not clinical qualification; absent contract is blocked, not local-success staff row. **Dependencies/tests:** FE-001/002/018/028/029, BG-015/020, DEC-02/03/04/11; least-privilege/lifecycle/revocation/credential secrecy tests.

<a id="fe-028"></a>

### FE-028 — Audit, retention and governed settings (blocked)

**User/preconditions:** approved audit/config/lifecycle permissions; generic admin cannot imply unlimited audit. **Route/navigation:** proposed admin audit/retention/settings/facility. **UI conditional on contracts:** read-only audit event/actor/target/time/outcome/correlation/request/causation/source plus safe details, supported filters/pages; no edit/delete audit. Retention approved policy/artifact classes/deletion result/backup exceptions; settings approved languages/fields/checklist/workflow/recipient/knowledge versions and change history. No provider secrets in browser; knowledge admin optional DEC-09.

**Flow/API:** scoped future reads; governed versioned/reasoned config changes; lifecycle operation only under disclosed policy with backend all-artifact verification. Append-only repository/trigger, internal KnowledgeService and runtime Settings do not provide administrative HTTP. **Backend contract required:** BG-017/018/019 permissions/read/page/lifecycle/governance.

**Acceptance:** forbidden entries never delivered; audit immutable; originals/derivatives/indexes/queues follow deletion contract and backup exceptions reported; no invented duration; config persists approved version; no token/key exposure; blob.delete is never presented as complete case erasure. **Dependencies/tests:** FE-002/021/027/029, BG-017–020, DEC-09/10/12; audit isolation/lifecycle/config review tests.

<a id="fe-029"></a>

### FE-029 — Shared validation, states, accessibility and design

**User/preconditions:** all roles/pages; §15.1 S1–S5 mandatory. **Route/navigation:** shared shell/primitives/forms/results/reference. **UI:** truthful loading/empty/disconnected/denied/consent/stale/failure; strict UUID/enum/length/integer checks; accessible errors/live status; source-aware responsive panels; Times New Roman including JSON/IDs; navy/teal and textual status semantics. Closed mobile drawer excluded from focus/modal sequence, dialogs trap/restore focus, file picker keyboard-operable. Every button works locally as described or is explicitly unavailable.

**Flow/API:** validate→announce loading→observe actual result; safe failure retains unsent current-view input; stale reload/reconcile; preserve case/source through navigation. Map verified error envelope; no assumption field-error arrays. **Acceptance:** unevaluated panel never “no conflict/missing”; fractions rejected; all controls keyboard named/error-associated; Escape/focus restoration works; no color-only status; narrow viewport preserves source/claim; safe401/403/404/409/413/415/422/500/503; no secrets or fabricated success. **Dependencies/tests:** foundation for all FE; DEC-11 client durability policy; later browser keyboard/a11y/responsive/error/refresh tests, not CSS-only WCAG claim.

<a id="fe-030"></a>

### FE-030 — Permission-aware overview

**User/preconditions:** current profile; widget requires matching readable contract. **Route/navigation:** existing dashboard, Overview. **UI:** permitted next actions/create case/open case/review queue/known task/handoff links; returned scope/limit stated. No unsupported hospital totals, wait/efficiency metrics, urgency ranking or fabricated fixtures. **Flow/API:** A31 where review:read, A30 only selected readable case; future broader indexes BG-002/014. No aggregate endpoint assumed.

**Acceptance:** denied widget absent; all links real/context-preserving; disconnected screen no invented totals; capped first 50 not full workload count; refresh rederives authorized state. **Backend contract required:** only if later approved aggregate requested. **Dependencies/tests:** FE-001/002/004/012/018/025/029; widget permission/limited-scope/navigation tests. P2 recommendation, not facility analytics expansion.

<a id="fe-031"></a>

### FE-031 — Optional permitted-content read-aloud

**User/preconditions:** authenticated active user; approved content/purpose/provider use DEC-03/06/07/10. Current TTS lacks case/consent gate, so clinical-content use not automatically authorized. **Route/navigation:** optional source/review read-aloud control. **UI:** deliberate play/stop/loading/failure, selected text≤4096, configured voice; generated speech distinct from original voice evidence; no autoplay.

**Flow/API:** deliberate user selection→A50 TextToSpeechRequest→binary audio→play/stop/temporary-object cleanup. No persisted case/audio artifact or streaming contract implied. **Backend contract required:** BG-023 if case/purpose/permission/lifecycle gates needed. **Acceptance:** empty/over4096 rejected; failure not called generated audio; no original-audio provenance claim; keyboard controls/text fallback; no retained speech beyond approved temporary policy; no automatic narrative transmission. **Dependencies/tests:** FE-001/002/006/010/029, DEC-03/06/07/10; purpose/playback/failure tests. P3, defer freely without blocking core prototype.

<a id="audit-section-16"></a>

## 16. Prioritization and implementation increments

P0 = critical prerequisite for safe/coherent workflow/access; P1 = core prototype workflow; P2 = supporting operation; P3 = optional/deferred. P0/P1 reasons are in §10. A backend prerequisite may be P0 while its administrative UI is P2. Priorities authorize neither backend changes nor integration in this audit.

| Increment | Requirements | Dependency / exit criteria |
|---|---|---|
| 0. Resolve critical contract/policy blockers | BG-001/003/004/006/010/011/012/018/020; DEC-01/02/03/05/07/10/11 | Agree permitted identity, scope, qualification, consent/read rules, scanning, run IDs, approval invalidation, early escalation and lifecycle policy. Backend owners produce contracts separately; frontend cannot compensate for missing enforcement |
| 1. Foundation and truthful access | FE-001/002/029 | Root login-first; session design approved; permission-aware routes/actions, genuine blocked states, common errors/validation/keyboard/focus/serif baseline; no fake authentication |
| 2. Subject, case, consent and encounter intake | FE-003–007 | BG-001/002/003/005/011; guided shared context, no title/MRN/urgency payload fiction; DP before narrative/upload; optional encounter scoped |
| 3. Reports, provenance and tasks | FE-008–013 | BG-004/005/006; uploads never falsely READY, inspectable originals, exact task/run/extraction distinction, manual safe input preserved |
| 4. Structuring and advisory presentation | FE-014–017 | BG-007/008/019, DEC-06/09; visible unknowns/conflicts/date uncertainty, approved corpus citations, bounded advisory/validation labels |
| 5. Mandatory review integrity | FE-018–022 | BG-005/008–011/015/020/022; exact edited content, neutral save versus explicit qualified approval, versions, return/manual fallback/reapproval |
| 6. Manual escalation | FE-023 | Review action available to specify earlier; BG-012 early bypass required before claiming FR-024/NFR-001 complete. Surface during intake once contract exists |
| 7. Approved referral and acknowledged handoff | FE-024–026 | BG-013/014/016, DEC-08; preview equals delivered content, queued/send/ack/complete separated, failure/read/ownership; simulated boundary explicit |
| 8. Bounded administration/support | FE-027/028/030 | BG-015–020, DEC-04/09/10/12; minimum prototype administration; no operational claim for blocked pages or invented dashboard aggregates |
| 9. Quality review/optional additions | All shared criteria; FE-031 optional | Browser accessibility/responsive/source-fidelity/recovery verification. Core error/accessibility work starts in increment 1; read-aloud remains P3 |
| 10. Backend integration after separate approval | §20 checklist | Approved requirement.md plus subsequent integration authorization; no APIs/adapters now |

After approval, frontend preparation can use verified schemas and deliberately unavailable states. Missing backend contracts block integrated acceptance; they never justify mock patients, fake success or browser-owned permissions. No delivery dates or clinical effectiveness estimates invented.

<a id="audit-section-17"></a>

## 17. Backend gaps and missing contracts

These are separately assigned dependencies, not backend implementation requests in this task. No new endpoint is represented as available. P0 entries are workflow/access/safety prerequisites.

| Gap ID | Evidence / required behavior or contract | Priority | Dependent FE |
|---|---|---|---|
| BG-001 | E-04/05: permitted synthetic subject create/lookup/name, consent relationship to user, explicit permitted-data class/real identifier rejection; patient-name optionality and lifecycle DEC-01 | P0 | 003/006/007 |
| BG-002 | E-01/05: scoped case list/search/filter/order/page/identity references; no existing list route/repository method | P1 | 004/009/030 |
| BG-003 | E-04: consent read/list/events/disclosure/data class, subject/facility authorization, duplicate/reconsent policy, missing-ID errors, withdrawal/read consequences | P0 | 003/006/017/024 |
| BG-004 | E-06/07: actual scanner, durable result task/callback/state transition, quarantine/failure recovery and blob/DB compensation; no force-ready or bypass | P0 | 008–013 |
| BG-005 | E-06/14: TEXT enum fix; public case evidence/raw text/derived reads, complete table/region/transcript/language/candidate locators, stable typed workspace | P1 | 007–014/019/024 |
| BG-006 | E-10/18: explicit task/ProcessingRun/ExtractionRun IDs, task result/status reconciliation, discovery, failed-run retry/idempotency and structured processor validation; preserve failed-run metadata across worker rollback and reconcile durable task failure with run discovery | P1 | 011–015/025 |
| BG-007 | E-08–11: complete demographic/report dates/values/units/table candidates, real language/provider scope, genuine STT timings, cross-evidence conflicts/date anchors/source links; current demo insufficient | P1 | 010/013–015 |
| BG-008 | E-11/15: registered selected-question/answer/provenance/round/stop/return workflow; durable state/owner/version/server bounds, not queue-only unregistered service | P1 | 015/020/022 |
| BG-009 | E-15: attributed field verify/correct/undo and manual note/template save/review independent of AI; ReviewerNoteORM not operational fallback | P1 | 007/013/014/022 |
| BG-010 | E-15: neutral edit versus accept; latest human content/version/history/diff; material-change invalidate/reopen/new approval; rejected-draft return. Workspace and referral currently differ | P0 | 019–024 |
| BG-011 | E-05/13/15: close generic case:write transition bypass of review/referral/ack closure invariants. Preserve the already-implemented AI REJECTED/DRAFT review-action guard; add regression evidence, not a new rejection capability | P0 | 002/004/017/020/021/024/025 |
| BG-012 | E-16: authorized manual escalation from intake/AI outage, independent of AI gate, owned read/history/ack/resolution and explicit authority | P0 | 022/023 |
| BG-013 | E-17: approved package content preview/read/history and current approval/version/evidence readiness checks through finalize/initiate/send; no stale/superseded transmission | P1 | 021/024/025 |
| BG-014 | E-17/18: handoff list/detail/version/failure/reference/history; fresh delivery permission/consent/approval/recipient; configured timeout/owner/followup, separate receipt/reject/accept if required | P1; fresh consent/approval P0 | 012/025/030 |
| BG-015 | E-03/05/14: minimal facility/staff lifecycle, scoped directory/eligible reviewers, individual credential/activate/disable and audited role assignment; multi-facility decision | P2; access-policy P0 | 002/003/018/027 |
| BG-016 | E-17: scoped recipient detail/config/CRUD/activation/audit; current global active id/name/type list only | P2 | 024–028 |
| BG-017 | E-19: audit-view permission/scoped paginated read/filter/safe details; never audit edit/delete | P2 | 028 |
| BG-018 | E-06/19: retention policy, whole artifact/index/cache/queue/temp lifecycle/delete, verification and backup/audit exceptions; blob.delete/cascades insufficient | P0 backend; P2 UI | 008/021/028 |
| BG-019 | E-10–13/21: approved source/corpus reads/governance, complete model/prompt/schema/retrieval/policy/case/note trace, reviewed language/checklist/workflow settings without browser secrets | P1 trace/source; P2 admin | 013–017/021/028 |
| BG-020 | E-03/14: qualified reviewer/technical admin separation, health_worker write-without-read mismatch, permission bound to same scoped granting role, null-facility/subject ownership/profile/action eligibility | P0 | 002/018–023/027/028 |
| BG-021 | E-02: optional recovery/password lifecycle/refresh; forgot-password cannot be integrated today; unavailable unless approved contract | P2 or defer | 001 |
| BG-022 | E-14: review queue public pagination/order/total/eligibility; current HTTP first 50 despite internal limit/offset | P1 | 018/030 |
| BG-023 | E-22: optional clinical-content TTS purpose/case/permission/provider/temporary lifecycle; auth-only not clinical disclosure | P3 | 031 |

Backend-only obligations: platform encryption, backups/recovery, incident/rollback/key rotation, malware isolation and provider retention need separate configuration/governance evidence. Key-based logging redaction is not free-text PHI detection. Many denial audits are appended before exceptions in request transactions and can roll back; durable AuthService append_security_event does not prove every denial persists. Verify negative-path audit persistence separately; this alone does not require another page.

<a id="audit-section-18"></a>

## 18. Product, clinical, security and architecture decisions required

No authoritative resolutions found. DEC IDs group implementation decisions without replacing PRD D01–D12.

| Decision | Required owner decision/evidence | PRD linkage | Impact |
|---|---|---|---|
| DEC-01 | Synthetic subject/user relationship, patient name/lookup/requiredness, permitted class/rejection, encounter timezone/source-date semantics | D01/D06 | BG-001; FE-003/005–007; no real MRN |
| DEC-02 | Qualified final reviewer, nurse/health_worker powers, historical reviewer writes, technical admin separation, assignment override | D02; FR-019/023/029; U p9 | BG-020; clinical actions; migration 0015 conflict |
| DEC-03 | Null/system-wide/multiple-role scope, subject consent authority, reads after withdrawal, queued external processing consent | D07/D08 | BG-003/014/020; FE-002/006/010/025 |
| DEC-04 | Minimum prototype staff/facility administration, individual invite/create/activate/disable mechanism/directory/membership | D01/D02; FR-033 | BG-015; FE-027; no hospital ERP expansion |
| DEC-05 | Early escalation authority/owner; urgency default Unassigned; only conditional approved local policy, technical vs clinical state | D03 | BG-011/012; FE-003/023/029 |
| DEC-06 | Approved English/Hindi, formats/provider combinations/dataset/quality, candidate fields/checklist/question wording | D04/D05/D06 | BG-007/019; FE-008/013–017 |
| DEC-07 | FR-011 Should vs SEC-003 Must scanning/isolation; effective MIME/size, previews/storage/provider privacy/failure recovery | D05/D07/D08 | BG-004/005/018; FE-008/010/031 |
| DEC-08 | Simulated recipient/channel, ack evidence/recorder, receipt/accept/reject distinction, timeout/followup owner/closure | D09 | BG-013/014/016; FE-024–026; no invented deadline |
| DEC-09 | Approved note schema/material changes/version trace, checklist/knowledge owner/publish/review and configuration authority | D02/D03/D04/D12; FR-021/030/033 | BG-010/019; FE-013/015–022/028 |
| DEC-10 | Disclosed retention/deletion timing/all derivatives/temp/index/task/backup and audit exceptions/verification | D08 | BG-018; FE-006/028/031 |
| DEC-11 | Browser/server token/refresh/recovery, reload/expiry/disable sessions, safe unsent-input durability | D07/D08; SEC-001/005 | FE-001/002/029; BG-015/021 |
| DEC-12 | DRES/PS03 authority, approval/release/incident owners, safe integration infrastructure/provider quality/a11y gates; live/interoperability separate | D10/D11/D12 | All readiness; no historical readiness generalization |

Clinical governance owns clinical authority/policy/question wording; security/privacy owns scope/consent/storage/lifecycle; product owns bounded workflows/fields; architecture owns contracts/session/version IDs. Frontend cannot silently decide these.

<a id="audit-section-19"></a>

## 19. Explicitly deferred and excluded features

**Excluded by PRD:** live patients/PHI; diagnosis/prescribing/treatment; autonomous final urgency/disposition; diagnostic imaging interpretation; consumer self-triage; regulatory/compliance/clinical-effectiveness claims; employer access to individual clinical feed. Missing evidence is never negative; conflicting candidates never silently merged.

**Documented deferred scope:** broad regional/dialect support, production handwriting, ABDM/ABHA/FHIR exchange/live referral networks, clinical pilot/deployment, facility analytics/workforce forecasting. Docker/Kubernetes/microservices/LangGraph/additional stores are excluded from documented release architecture, not frontend gaps.

**Optional:** adjacent diff FR-022 Should after history; minimal approved facility config FR-033 Should; FE-030 overview/FE-031 read-aloud; realtime push unnecessary with completed polling. Optional scope does not weaken SEC-003 scanning or FR-032 lifecycle. Conditional urgency is not mandatory case creation priority.

**Required core gaps not automatically deferred:** synthetic identity/disclosure, scanning/results, field correction/manual fallback/clarification bounds, safe approval/reapproval, early manual escalation, current approved package integrity, owned acknowledged handoff. Only authoritative scope approval can defer them.

<a id="audit-section-20"></a>

## 20. Phase 10 integration-readiness checklist

Future authorization gate only. Existing contract verified means traced source, not live integration. Missing-contract labels block complete workflow acceptance even where commands exist.

| Workflow | Integration classification | Exact dependency before integration |
|---|---|---|
| [FE-001](#fe-001) auth | Permission or policy decision required | A01–03 traced; DEC-11; BG-021 only recovery |
| [FE-002](#fe-002) access | Permission or policy decision required | BG-020/DEC-02/03 facility/profile/action rules |
| [FE-003](#fe-003) identity/create | Backend contract missing | A07 verified; BG-001/003 identity/disclosure/initial lifecycle |
| [FE-004](#fe-004) case list/detail | Existing contract partially verified | A08/A10/A12; BG-002 list/BG-011 transitions |
| [FE-005](#fe-005) encounters | Existing contract verified | A11/A12 schema/service/repo/test source; DP/scope/time; runtime unexecuted |
| [FE-006](#fe-006) consent | Backend contract missing | A04–06 partial; BG-003 scope/read/disclosure/reconsent |
| [FE-007](#fe-007) narrative | Existing contract partially verified | A13; BG-005 TEXT response/read; BG-009 corrections |
| [FE-008](#fe-008) upload | Backend contract missing | A14; BG-004 actual scanner/recovery; DEC-06/07 format/config |
| [FE-009](#fe-009) inventory | Backend contract missing | BG-005 list/raw; A15 metadata |
| [FE-010](#fe-010) source preview | Existing contract partially verified | A16 READY-only; BG-004/005/007 locator/time/read policy |
| [FE-011](#fe-011) processing | Existing contract partially verified | A17–19; BG-006 result IDs/retry/READY/provider scope |
| [FE-012](#fe-012) tasks | Backend contract missing | A29/A30 status; BG-006 results/recovery/dispatcher/worker |
| [FE-013](#fe-013) fields | Backend contract missing | BG-005/007/009 full reader/provider/correction; DEC-06 |
| [FE-014](#fe-014) timeline/conflict | Existing contract partially verified | A20–22/25; BG-006 ID/BG-007 candidates/date semantics |
| [FE-015](#fe-015) gaps/questions | Existing contract partially verified | A23–25 first-round; BG-008 interaction/BG-019 checklist |
| [FE-016](#fe-016) retrieval | Existing contract partially verified | A26/A27; BG-019 approved corpus/source/governance |
| [FE-017](#fe-017) advisory | Existing contract partially verified | A28; BG-019 metadata/read/BG-011 safe approval; provider DEC-07 |
| [FE-018](#fe-018) queue | Backend contract missing | A31–35; BG-015 directory/BG-022 pages/DEC-02 authority |
| [FE-019](#fe-019) workspace | Existing contract partially verified | A36; BG-005/010 complete sources/latest human content |
| [FE-020](#fe-020) final review | Permission or policy decision required | BG-010/011 neutral edit/reapproval/general transition fixes; preserve existing rejected-output gate; DEC-02 |
| [FE-021](#fe-021) history/reapproval | Backend contract missing | BG-010/019 exact approved content/version and policy |
| [FE-022](#fe-022) fallback/clarify | Backend contract missing | BG-008/009/010 persisted human note/answers/stop/return |
| [FE-023](#fe-023) escalation | Existing contract partially verified | A41/A42; BG-012 early bypass/owner/read; DEC-05 |
| [FE-024](#fe-024) referral | Backend contract missing | A43/A44; BG-013 preview/current approval/readiness |
| [FE-025](#fe-025) handoff | Backend contract missing | A45–48; BG-006/013/014 read/version/consent/followup; demo-only |
| [FE-026](#fe-026) recipients | Existing contract partially verified | A49 selection; BG-016 scope/CRUD/DEC-08 |
| [FE-027](#fe-027) staff/facility | Backend contract missing | BG-015/020; DEC-02/04/11; CLI not general onboarding |
| [FE-028](#fe-028) audit/settings | Backend contract missing | BG-017–019 read authority/retention/governance |
| [FE-029](#fe-029) shared quality | Existing contract partially verified | Core error envelope; future browser/session/access/refresh tests |
| [FE-030](#fe-030) overview | Existing contract partially verified | Individual A31/A30; no aggregate; BG-002/014 indexes if requested |
| [FE-031](#fe-031) read-aloud | Deferred by product scope | P3 recommendation; if approved Provider/configuration decision required and BG-023 |

Before Phase 10:

- [ ] User approves requirement.md and later implementation/integration scope separately.
- [ ] DEC-01–12 resolved as applicable; exact DRES/PS03 obtained or limitations accepted.
- [ ] P0 safety/access/consent/approval/scan/lifecycle dependencies have source and negative-path tests; generic transitions cannot bypass clinical/ack gates.
- [ ] Actual migration head/role mappings confirmed in approved infrastructure, not assumed from R8 migration 0013.
- [ ] Chosen revision API contracts include real ID meanings/errors/consent/scope/qualification/state/version/source locators.
- [ ] Public identity→notice/consent→case/encounter→text/file→scan→results→review tested; seeded READY evidence does not substitute for upload coverage.
- [ ] Edited display/approval/transmitted content equality, invalidation and unsafe-AI rejection verified.
- [ ] Provider choices/dispatcher/worker/recovery and task-versus-run terminal semantics/bounded polling agreed.
- [ ] Simulated send/failure/ack/complete/withdrawal-before-delivery tested; unresolved handoff has owner.
- [ ] All-artifact retention/delete/backup/audit exceptions verified; no keys/signed URLs/raw content logged.
- [ ] Keyboard/error/focus/contrast/responsive/source/refresh tests; no unproven WCAG/clinical/compliance claim.
- [ ] No missing-contract-dependent UI action labeled available/successful.

<a id="audit-section-21"></a>

## 21. Evidence references and unresolved audit limitations

Sources are actual inspected artifacts relative to this frontend document. Symbols listed exist in source; schemas in §6 provide exact contract fields. PDF sources remain external; no invented line numbers.

| Evidence | Actual sources / principal symbols | Test evidence and limits |
|---|---|---|
| E-01 Composition/API | [main.py](../src/careintel/main.py) create_app/lifespan; [router.py](../src/careintel/api/v1/router.py); [deps.py](../src/careintel/api/deps.py); every api/v1/*/router.py and its schemas | [test_scaffold_capabilities.py](../tests/api/test_scaffold_capabilities.py) registration/permission/version-schema, not full workflows |
| E-02 Auth | [auth_service.py](../src/careintel/application/auth/auth_service.py) AuthService; token_service.JWTService; password_hasher.PasswordHasher; session/user models and repositories; auth API | tests/unit/test_auth.py and test_security.py; integration admin bootstrap login path; none executed |
| E-03 RBAC/admin | [policy.py](../src/careintel/domain/auth/policy.py) AuthorizationPolicy.evaluate; auth roles/permissions/UserContext; [0015](../migrations/versions/0015_seed_role_permissions.py) plus 0002/0003/0004/0005/0014; UserRoleORM; [admin_bootstrap_service.py](../src/careintel/application/auth/admin_bootstrap_service.py); scripts/bootstrap_admin.py/seed_dev_admin.py | Unit/integration admin and auth tests; current applied role assignments unverified |
| E-04 Consent | [consent_service.py](../src/careintel/application/auth/consent_service.py); ConsentPolicy.require_active, ConsentPurpose; ConsentORM.subject_id; consent_repo; consent router/schemas | unit/test_consent.py, test_auth.py, evidence consent tests; read/object-management contract absent |
| E-05 Cases/encounters | [case_service.py](../src/careintel/application/case/case_service.py) create_case/get_case/transition_state/get_state_history; [encounter_service.py](../src/careintel/application/case/encounter_service.py); cases API; domain/case commands/models/states/state_machine; case/encounter/history/outbox ORM/repos | api/test_cases.py mocks; case state/encounter unit tests; older golden path only case creation |
| E-06 Evidence/scanner | [evidence_service.py](../src/careintel/application/evidence/evidence_service.py) register/start/complete/read/list/download; [file_validator.py](../src/careintel/application/evidence/file_validator.py); evidence API; EvidenceModality/StateMachine; evidence/text/history/outbox ORM/repos; [noop_scanner.py](../src/careintel/infrastructure/scanner/noop_scanner.py), main binding/default Settings | API evidence tests mock service/lowercase responses; unit file/state/consent/security. They do not verify service TEXT response or scan completion |
| E-07 Storage | [AzureBlobProvider](../src/careintel/infrastructure/storage/azure_provider.py); storage port/fake provider; evidence secure download | Infrastructure/fake blob tests; no external privacy/container/SAS call here |
| E-08 OCR | [document_processor.py](../src/careintel/application/processing/document_processor.py); [AzureDocumentIntelligenceProvider](../src/careintel/infrastructure/ocr/azure_provider.py); OCR port/demo; processing ORM/repo | Unit document processor normal/idempotent/not-ready/modality/provider failures; no current table/scan-quality evaluation |
| E-09 STT | [speech_processor.py](../src/careintel/application/processing/speech_processor.py); [AzureSpeechProvider](../src/careintel/infrastructure/stt/azure_provider.py); transcript models/repo | Speech processor and Azure speech request-format tests; fallback interval is source behavior, not measured provenance |
| E-10 Language/extraction/runs | [ProcessingService](../src/careintel/application/processing/processing_service.py) trigger/execute/get_run/_source_run_id/_text_from_source_run; access/language/extraction processors; [DemoExtractionProvider](../src/careintel/infrastructure/extraction/demo_provider.py); language/translation demo, main/worker wiring; processing ORM/repo/API | Unit processing suites and persisted recovery test source; configuration strings do not wire real language/extraction providers |
| E-11 Structuring | [StructuringService](../src/careintel/application/structuring/structuring_service.py); temporal/conflict/missing/question/checklist modules, demo_v1.json, structuring models/repo; [router/schemas](../src/careintel/api/v1/structuring/router.py) | Unit temporal/conflict/missing/question; integration structuring API only auth; recovery source persisted subset |
| E-12 Knowledge/retrieval | [KnowledgeService](../src/careintel/application/knowledge/knowledge_service.py), chunker/embedding; [RetrievalService](../src/careintel/application/retrieval/retrieval_service.py), dense/sparse/fusion, NoOpReranker; knowledge/retrieval ORM/repos/API | Unit chunker/fusion/embedding/retrieval success/failure/scope; API mocks; current approved corpus not verified |
| E-13 AI | [AIWorkflowService](../src/careintel/application/ai/ai_workflow_service.py); AIService/AIContextBuilder/output_validation/PolicyService; domain AI models/status; Azure/demo LLM; AI ORM/repo/API | Unit AI/context/schema/policy/security; fixture-limited source and sanitization proof, no clinical effectiveness |
| E-14 Review/workspace | [ReviewService](../src/careintel/application/review/review_service.py) list/enter/_eligible_reviewer/assign/reassign/start; [WorkspaceService](../src/careintel/application/review/workspace_service.py); ReviewAccessGuard; review model/repo/state/API | R5 queue/assignment/workspace/isolation source; reviewer eligibility mocked, not clinical qualification |
| E-15 Draft/decision/clarification | [DraftReviewService](../src/careintel/application/review/draft_service.py) _locked_context/accept/reject/edit; [ReviewDecisionService](../src/careintel/application/review/decision_service.py); [ClarificationService](../src/careintel/application/review/clarification_service.py); DraftEditVersionORM/ReviewerNoteORM | R5 asserts edit→APPROVED and referral latest human content; no neutral-save/invalidation proof. Clarification unregistered |
| E-16 Escalation | [EscalationService](../src/careintel/application/escalation/escalation_service.py); review escalation states/records/repo; escalation API | R5 create/resolve, API schema/version tests; no early intake/ack/followup |
| E-17 Referral/handoff/recipients | [ReferralPackageService](../src/careintel/application/handoff/referral_service.py); [HandoffService](../src/careintel/application/handoff/handoff_service.py); RecipientService; handoff states/ORM/repo/API | [test_handoff_security.py](../tests/unit/test_handoff_security.py), R5 ack/completion source; no current full public journey execution |
| E-18 Async/events | [UnifiedOutboxDispatcher](../src/careintel/application/workflow/outbox_dispatcher.py); AsyncTaskService/repo/model/state; tasks API; [executor.py](../src/careintel/workers/executor.py); workers context/providers/services/celery_app/outbox_runner and processing/retrieval/AI/workflow/handoff handlers | R4 async/Celery source and task/config units; no current scheduler/heartbeat deployment verified; API lacks results |
| E-19 Audit/privacy | [AuditRepository](../src/careintel/persistence/repositories/audit_repo.py) append/append_security_event; AuditLogORM/events; [0013](../migrations/versions/0013_audit_immutability_observability.py) trigger; core/logging.redact_sensitive_data; storage delete | R6 UPDATE/DELETE denial/redaction source; current trigger application and retention unverified |
| E-20 Workflow tests | [test_recovery_stages_1_3.py](../tests/integration/test_recovery_stages_1_3.py); [R5](../tests/integration/test_recovery_r5_human_workflow.py); [golden_path](../tests/e2e/test_golden_path.py); tests/conftest.py | Full service test seeds READY inputs/providers/actors; golden stops at case. Conftest may load real .env; suite deliberately not executed |
| E-21 Core/ops | core/config/database/errors/logging/correlation; [health service](../src/careintel/api/v1/health/service.py); scripts backend_runtime/verify_runtime/verify_infra/verify_providers/verify_audit_integrity/verify_auth_live/verify_tts_api, setup/startup scripts, pyproject/uv lock | Health/errors/logging/config/startup/script tests; operational/provider scripts can write fixtures/call providers, not run |
| E-22 TTS | [SpeechService](../src/careintel/application/audio/speech_service.py); [audio router](../src/careintel/api/v1/audio/router.py); infrastructure/tts port/Azure/demo | tests/api/v1/test_audio_router.py and application/audio/test_speech_service.py; auth/length/provider, no purpose-bound case use |
| E-23 Frontend | [app](src/app), [components](src/components), all 13 pages/auth/shell layouts/feature handlers/17 UI files; [globals.css](src/app/globals.css), package/components.json/types/navigation/lib/utils/README/AGENTS | No frontend tests/API client/session/middleware found; local timers inspected; browser/build not run; external unused-import edit preserved |
| E-24 Documents | [PRD](/home/lucifer/Downloads/CareIntel_Product_Requirements_Document_v1.pdf); [problem baseline](/home/lucifer/Downloads/CareIntel_Master_Problem_Understanding.pdf); [README](../README.md), [STARTUP](../STARTUP.md), [RELEASE_EVIDENCE](../RELEASE_EVIDENCE.md) | Historical R8 outcomes from 30 September/source/migration 0013, not results executed now |

### Test evidence interpretation

Unit/API suites commonly mock repositories/providers/services/user dependencies; passing such tests would only prove asserted fixture behavior. R4/R5/R6/recovery integration sources exercise meaningful durable and audit paths but need external database (Celery also Redis) and create test records, so none executed here. Older golden path explicitly stops before processing. R8 historical passes retain seeded-input/quality/load limits; they do not override current source gaps.

### Unresolved audit limitations and change verification

1. DRES and original PS03 unavailable after repository/project/document search; exact source sections/IDs unverified. PDFs extracted to /tmp for reading, originals unchanged. Other project copies and private cloud documents not assumed authoritative.
2. No APIs/provider calls/current database schema/permission/container/configuration reads, worker execution, tests or browser checks. Applied head, runtime behavior, throughput, language quality, accessibility and provider retention remain Unverified.
3. No credentials/environment values/report or patient contents inspected or disclosed. Code defaults/selectors are not configured runtime evidence.
4. Initial working tree was clean. During read-only inspection, an unrelated removal of unused ReviewQueueBadge import appeared in frontend/src/components/review/review-queue-list.tsx. This audit did not make, undo or extend it; component re-read afterwards. Final diff distinguishes it from the audit-created document.
5. Only audit-created repository artifact is frontend/requirement.md. No application/test/migration/dependency/lock/environment/configuration/existing-document edits by this task. Final read-only checks confirmed only the new deliverable and that separate one-line external import removal in the working tree; no other tracked modification or additional untracked deliverable. All 52 documented method/path pairs match static router extraction, all local evidence links resolve, IDs are unique/defined, and sections 1–21 are ordered. Application tests were not executed.

### Derived inventory and gap counts

Section9 has 65 backend capability rows: **14 Implemented and verified**, **36 Partially implemented**, **8 Documented only**, **7 Unsupported**. Thus **50 rows have source implementation** with explicit limitations; 65 inventoried does not mean 65 complete implementations.

Across **68 gap-matrix rows** (65 backend plus 3 foundation): **12 Frontend gap**, **2 Frontend enhancement**, **12 Backend gap**, **8 Backend contract gap**, **24 Cross-layer gap**, **3 Security or permission gap**, **1 Product decision required**, **6 No gap identified**. Primary row counts disjoint. Reportable confirmed frontend work = **14 gap/enhancement rows**; backend gaps = **20 backend/contract rows**; cross-layer = **24**; **four security/product rows require unresolved control/decision work**. Separately **12 DEC decision groups**, **23 BG dependencies**, **31 FE requirements** are linked work groupings, not extra additive feature counts. Source-document/runtime limitations are Unverified evidence, not invented features.
