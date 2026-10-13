# CareIntel — Frontend Gap & Backend Blocker Report
## Phases 1–4 Architectural Analysis & Contract Inconsistencies

**Repository:** `CareIntel`  
**Document Location:** `/home/lucifer/Desktop/CareIntel/frontend/frontend-gap-report.md`  
**Scope:** Gaps identified across Identity, Cases, Consent, Intake, Evidence, Processing, and Clinical Intelligence  
**Author:** Staff Frontend Architect & Healthcare Workflow Specialist  

---

## 1. Executive Summary

During the Phase 1–4 frontend implementation of CareIntel, all user interface views, sub-routes, and contract validation forms were brought into strict alignment with `requirement.md` specifications.

Crucially, **no mock data, fake persistent storage, or fabricated clinical entities** were introduced. Where backend endpoints are missing, unregistered, or architecturally misaligned, the frontend explicitly surfaces truthful, informative boundary notices with exact blocker IDs (e.g. `BG-xxx`, `DEC-xx`).

This report provides the exhaustive inventory of backend capability gaps and contract discrepancies that require backend engineering remediation before end-to-end integration can proceed.

---

## 2. Exhaustive Gap Analysis (BG-001 through BG-021)

### BG-001: Synthetic Subject Provisioning & Lookup Missing
- **Affected Requirements:** FE-003 (Case Creation), FE-004 (Case Details)
- **Current Backend Reality:** The backend database schema (`UserORM`) describes staff login credentials (`display_name`, `email`, `password_hash`). `CaseORM` contains a foreign key to a subject UUID, but there is **no subject creation API, no synthetic subject registry, and no search/lookup endpoint**.
- **Frontend Mitigation:** The legacy `CaseForm` mistakenly collected patient demographics (`patientId`, MRN, title, clinical priority). This was completely replaced with a contract-pure form requiring `synthetic_subject_id` UUID with RFC 4122 regex validation.
- **Remediation Required:** Implement `POST /api/v1/subjects` and `GET /api/v1/subjects/{id}` with synthetic cohort metadata.

---

### BG-002: General Case List / Search Endpoint Missing
- **Affected Requirements:** FE-004 (Case Roster)
- **Current Backend Reality:** The backend contract provides `GET /api/v1/cases/{id}` to fetch an individual case by UUID, but **`GET /api/v1/cases` (list/filter cases) does not exist**.
- **Frontend Mitigation:** The case roster table was updated with contract columns (`case_id`, `synthetic_subject_id`, `state`, `version`, `created_at`). An exact UUID lookup input was added, allowing clinicians to navigate directly to `/cases/{id}` without fabricating a mock list.
- **Remediation Required:** Implement `GET /api/v1/cases` supporting pagination (`limit`, `offset`), state filtering (`CaseState`), and date ranges.

---

### BG-003: Consent Ledger Query & Ingestion Endpoints Missing
- **Affected Requirements:** FE-003 (Case Form validation), FE-006 (Consent Panel)
- **Current Backend Reality:** `CreateCaseRequest` strictly requires a `consent_id` UUID. However, the backend provides **no endpoint to read consent status (`GET /api/v1/consents/{id}`) or create a consent grant (`POST /api/v1/consents`)**.
- **Frontend Mitigation:** Created `/cases/[id]/consent` displaying the 3 mandatory consent purposes (`data_processing`, `ai_analysis`, `referral`) with notice version 1.0. All interactive buttons (Capture, Withdraw) are visibly disabled with clear BG-003 notices, preventing deceptive simulated checkboxes.
- **Remediation Required:** Implement the Consent management resource router with purpose-specific validation.

---

### BG-004: NoOpScanner Active — Files Trapped in `STORED` State
- **Affected Requirements:** FE-008 (File Evidence Upload), FE-009 (Evidence List), FE-010 (Evidence Preview)
- **Current Backend Reality:** Binary file uploads enter the `STORED` state in MinIO object storage. The active backend scanner is `NoOpScanner`. Because no antivirus or content scanner is configured, **files cannot transition from `STORED` to `READY`**. Downstream processors and file downloads require `READY` state.
- **Frontend Mitigation:** Added `EvidenceStateIndicator` in the evidence workspace visually highlighting the `STORED` gate and explaining that file execution is safely quarantined until an external scanner service is attached.
- **Remediation Required:** Configure an asynchronous scanning worker (e.g. ClamAV daemon) that issues state transitions from `STORED` to `READY` or `QUARANTINED`.

---

### BG-005: Evidence List Route Unregistered & TEXT Modality Capitalization Mismatch
- **Affected Requirements:** FE-007 (Narrative Intake), FE-008 (Text Evidence), FE-009 (Evidence Ledger)
- **Current Backend Reality:**
  1. `GET /api/v1/cases/{id}/evidence` is not registered on the backend router. Evidence is only queryable by direct ID (`GET /api/v1/evidence/{id}`).
  2. The `EvidenceModality` enum in the backend serializes text evidence as uppercase `"TEXT"` in certain endpoints, while client contracts and OpenAPI schemas specify lowercase `"text" | "document" | "image" | "audio"`.
- **Frontend Mitigation:** Handled both uppercase and lowercase modality variants gracefully in UI normalizers; documented the unregistered list endpoint in `EvidenceList`.
- **Remediation Required:** Register `GET /api/v1/cases/{id}/evidence` on the API router and enforce lowercase enum serialization across all response models.

---

### BG-006: AsyncTaskResponse Omits Result Payload & Extraction Run Unmapped
- **Affected Requirements:** FE-011 (Processing Pipeline), FE-012 (Task Status), FE-013 (Extraction Display)
- **Current Backend Reality:** When processing runs (OCR, transcription, extraction) are triggered, the returned `AsyncTaskResponse` contains `task_id`, `task_type`, `entity_id`, and `status`. However, **the actual execution result or generated `run_id` is omitted from the task envelope**, preventing direct client polling for results.
- **Frontend Mitigation:** `TaskStatusPanel` renders exact contract columns and status badges without fake progress bars or imaginary percentages. `ProcessingTriggerForm` explicitly requests `source_processing_run_id` for normalization and extraction tasks.
- **Remediation Required:** Include `result_entity_id` / `run_id` in `AsyncTaskResponse` or implement `GET /api/v1/tasks/{id}/result`.

---

### BG-007: Demo-Only Candidate Extraction Rules & No Cross-Evidence Conflicts
- **Affected Requirements:** FE-013 (Candidate Extraction), FE-014 (Timeline & Conflicts)
- **Current Backend Reality:** Candidate extraction currently executes rudimentary demo rules (extracting only fever symptoms and ISO date formats). Automated cross-evidence conflict detection between multiple medical records is not wired into the processing worker.
- **Frontend Mitigation:** Replaced misleading "No Conflicts Detected" empty state with "Conflicts Not Yet Evaluated". Displayed explicit notices on `ExtractionDisplay` indicating demo limitations.
- **Remediation Required:** Implement cross-evidence fact synthesis in the extraction engine to populate `ClinicalConflict` entities.

---

### BG-008: Clarification Questionnaire Ingestion Endpoints Missing
- **Affected Requirements:** FE-015 (Missing Information & Clarification Questions)
- **Current Backend Reality:** The structuring pipeline generates targeted follow-up inquiries (bounded to max 3 questions/round, 2 rounds). However, **endpoints to submit answers, stop questioning, or return to intake (`POST /api/v1/cases/{id}/clarifications/answer`) are completely missing**.
- **Frontend Mitigation:** Clarification questions are rendered in strict **display-only mode** with an informational banner for qualified reviewers.
- **Remediation Required:** Implement clarification lifecycle endpoints to accept clinician/subject answers.

---

### BG-009: Clinician Candidate Field Correction API Missing
- **Affected Requirements:** FE-013 (Extracted Field Verification)
- **Current Backend Reality:** Extracted candidate fields display verification statuses (`UNVERIFIED`, `VERIFIED`, `REJECTED`). However, there is no endpoint allowing clinicians to edit normalized values or dispute model-extracted facts before triage synthesis.
- **Frontend Mitigation:** Rendered candidate fields with status badges and provenance links; disabled interactive overrides pending backend mutation support.
- **Remediation Required:** Implement `PATCH /api/v1/evidence/extractions/{field_id}` supporting reviewer attribution and audit logging.

---

### BG-010: Neutral Review Edit vs. Auto-Approve Ambiguity
- **Affected Requirements:** FE-017 (AI Advisory Drafts), FE-020 (Review Workspace)
- **Current Backend Reality:** Modifying an AI-generated draft automatically marks it as approved in existing backend handlers, rather than preserving a neutral draft state with explicit attribution.
- **Frontend Mitigation:** AI drafts are quarantined when rejected, and advisory badges clarify that edits require explicit clinician sign-off.
- **Remediation Required:** Separate draft editing (`PUT /api/v1/drafts/{id}`) from human review approval (`POST /api/v1/drafts/{id}/approve`).

---

### BG-011: Case Lifecycle State Machine Orchestration Gap
- **Affected Requirements:** FE-003, FE-004 (Case Transitions)
- **Current Backend Reality:** Transitioning a case from `CREATED` to `CONSENTED` or `INPUT_RECEIVED` requires backend orchestration between multiple services that are currently decoupled.
- **Frontend Mitigation:** Clear state badge indicators and informational tooltips explain required state transitions.

---

### BG-012: Early Escalation State Gate Restriction
- **Affected Requirements:** FE-023 (Clinical Escalations)
- **Current Backend Reality:** Escalations are only permitted when a case is in `REVIEW_PENDING` or `REVIEWED` state, preventing urgent escalation during early intake or processing failures.
- **Frontend Mitigation:** Documented state prerequisites in escalation views.

---

### BG-015: Staff & Facility Discovery Directory Missing
- **Affected Requirements:** FE-003 (Optional `facility_id`), FE-027 (Staff Directory)
- **Current Backend Reality:** No endpoint exists to search or validate healthcare facilities or assigned clinicians.

---

### BG-019: Retrieval Source Passage Chunks Omitted
- **Affected Requirements:** FE-016 (Guideline Knowledge Retrieval)
- **Current Backend Reality:** Knowledge retrieval returns document titles and scores, but omits chunk text snippets and exact page citations.
- **Frontend Mitigation:** Labeled retrieval scores strictly as search relevance metrics (not clinical confidence) and noted snippet unavailability.

---

### BG-020 & BG-021: Session Authentication & RBAC Enforcement Missing
- **Affected Requirements:** FE-001, FE-002 (Permission Shell)
- **Current Backend Reality:** No active session middleware or permission checks are enforced across API endpoints.
- **Frontend Mitigation:** Disconnected session indicators presented on login and dashboard shells.

---

## 3. Core Architectural Decisions (DEC-01, DEC-03, DEC-05)

### DEC-01: Synthetic Subject & Case Model (No Patient Demographics)
- **Mandate:** CareIntel operates exclusively on de-identified or synthetic cohorts. The case schema stores only `synthetic_subject_id`, `consent_id`, and `facility_id`.
- **Frontend Enforcement:** The client form does not solicit patient name, date of birth, sex, telephone, address, department, or MRN. Clinical priority is unassigned until clinician assessment.

### DEC-03: Strict Notice Versioning & Purpose Isolation
- **Mandate:** Consent is not a blanket checkbox. It is partitioned into three independent purposes (`data_processing`, `ai_analysis`, `referral`), each tied to notice version 1.0.
- **Frontend Enforcement:** The consent workspace provides dedicated purpose cards with explicit lifecycle states.

### DEC-05: Non-Diagnostic Advisory Principle & Temporal Ordering Rules
- **Mandate:** AI drafts are strictly advisory and non-diagnostic. Events with `UNKNOWN` temporal bounds must never be silently sorted into a timeline.
- **Frontend Enforcement:** Unanchored temporal events are segregated from chronological bounds, and AI drafts feature prominent safety quarantine banners.

---

## 4. Remediation Checklist for Backend Team

1. [ ] Implement `POST /api/v1/cases` with active consent and subject validation.
2. [ ] Register `GET /api/v1/cases` and `GET /api/v1/cases/{id}/evidence` on the API router.
3. [ ] Configure scanner worker to advance `STORED` files to `READY`.
4. [ ] Include `run_id` and result references in `AsyncTaskResponse`.
5. [ ] Normalize `EvidenceModality` enum to lowercase `"text"` across all schemas.
6. [ ] Implement `POST /api/v1/consents` and `GET /api/v1/consents/{id}`.
7. [ ] Implement clarification questionnaire answer endpoints (`BG-008`).
8. [ ] Implement candidate field correction endpoint (`BG-009`).
