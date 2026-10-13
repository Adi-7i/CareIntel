# CareIntel — Master Frontend Implementation Tracker
## Phases 1–4 (FE-003 through FE-017) + Cross-Cutting Foundations

**Repository:** `CareIntel`  
**Location:** `/home/lucifer/Desktop/CareIntel/frontend`  
**Architecture:** Next.js 16.4.0 (Turbopack, App Router), React 19.3.0, TypeScript 5, Tailwind CSS v4, Base UI / Shadcn primitives  
**Aesthetic Standard:** Classical Clinical Typography (Times New Roman), Clinical Navy (`#16324F`) & Healthcare Teal (`#0F766E`)  
**Status:** Phases 1–4 Implementation Completed & Verified  

---

## 1. Quality Assurance & Verification Summary

| Gate | Target | Result | Verification Notes |
|---|---|---|---|
| **ESLint (`pnpm lint`)** | Zero errors, zero warnings | ✅ Passed (Exit Code 0) | Full repository scan clean across all 85+ components and routes. |
| **TypeScript / Turbopack (`pnpm build`)** | Zero compilation or type errors | ✅ Passed (Exit Code 0) | All 20 routes generated, strict domain typing in `src/types/index.ts`. |
| **API Discipline** | Zero unapproved mock data or fetch calls | ✅ Verified | No fabricated patient demographics, fake timestamps, or persistent storage hacks. |
| **Design Integrity** | Times New Roman & Clinical Navy/Teal | ✅ Preserved | All new interfaces adhere strictly to typography and color tokens. |

---

## 2. Requirement-by-Requirement Implementation Matrix

### Phase 1: Identity, Case Lifecycle, Consent & Encounters (FE-003 – FE-007)

| Requirement ID | Specification | Status | Implementation Details & Files | Contracts & Blockers |
|---|---|---|---|---|
| **FE-001** | Global Navigation & Shell Layout | ✅ Implemented | Sidebar navigation, header, theme styling, design system tokens preserved in `src/components/layout/app-sidebar.tsx`. | Cross-cutting; DEC-02 |
| **FE-002** | Role-Gated Capability Shell | ⚠️ Frontend Ready | Sidebar shows full operational surface; explicit notice that RBAC is unauthenticated in frontend mode. | BG-020, BG-021 |
| **FE-003** | Contract-Aligned Case Creation | ✅ Implemented | Replaced legacy form in `src/components/cases/case-form.tsx`. Collects strictly `synthetic_subject_id` (UUID), `consent_id` (UUID), and optional `facility_id` (UUID). Regex validation, synthetic model explanation, urgency unassigned disclosure. | `CreateCaseRequest` → `CaseResponse`; BG-001, BG-011, DEC-01 |
| **FE-004** | Case Roster & Detail Workspace | ✅ Implemented | Updated `src/components/cases/case-list.tsx` with contract columns (`case_id`, `synthetic_subject_id`, `state`, `version`, `created_at`) and exact UUID lookup. Updated `src/app/(shell)/cases/[id]/page.tsx` and `src/components/cases/case-details.tsx` to consume dynamic route `params.id` and render sub-route tabs. | `CaseResponse`; BG-002 |
| **FE-005** | Clinical Encounter Ledger & Intake | ✅ Implemented | Created `src/components/cases/encounter-form.tsx` (`encounter_type` 1-100, `occurred_at` ISO datetime, `notes` ≤2000 chars) and `src/components/cases/encounter-list.tsx` ledger. | `CreateEncounterRequest`, `EncounterResponse`; BG-005 |
| **FE-006** | Granular Consent Management Panel | ✅ Implemented | Created route `/cases/[id]/consent` and `src/components/cases/consent-panel.tsx`. Displays three distinct purposes (`data_processing`, `ai_analysis`, `referral`), notice version 1.0, lifecycle machine, and advisory non-diagnostic disclosure. | `ConsentResponse`, `ConsentPurpose`; BG-003, DEC-03 |
| **FE-007** | Clinical Narrative Free-Text Intake | ✅ Implemented | Created `src/components/cases/narrative-form.tsx` and unified intake route `/cases/[id]/intake/page.tsx`. Validates verbatim text up to 20,000 characters with live counter, BCP-47 language tag, and encounter binding. | `NarrativeIntakeRequest`; BG-005 |

---

### Phase 2: Multimodal Evidence & Document Workspace (FE-008 – FE-010)

| Requirement ID | Specification | Status | Implementation Details & Files | Contracts & Blockers |
|---|---|---|---|---|
| **FE-008** | Binary File & Text Evidence Ingestion | ✅ Implemented | Enhanced `src/components/evidence/file-evidence-form.tsx` and `src/components/evidence/text-evidence-form.tsx`. Supports route case context, lowercase modalities (`text`, `document`, `image`, `audio`), 50 MiB size limit, and NoOpScanner notice. | `CreateEvidenceRequest`, `EvidenceModality`; BG-004, BG-005 |
| **FE-009** | Multimodal Evidence Register | ✅ Implemented | Created `src/components/evidence/evidence-list.tsx` and `src/components/evidence/evidence-state-indicator.tsx`. Renders all 12 `EvidenceResponse` fields and visually conveys the quarantine scanning pipeline. | `EvidenceResponse`, `EvidenceState`; BG-004, BG-005 |
| **FE-010** | Evidence Inspection & Preview Panel | ✅ Implemented | Created `src/components/evidence/evidence-preview-panel.tsx` and unified workspace route `/cases/[id]/evidence/page.tsx`. Gated artifact downloads pending `READY` state; transparent binary preview blocker. | `EvidenceResponse`; BG-004, BG-005 |

---

### Phase 3: Processing Pipelines, Tasks & Candidate Extraction (FE-011 – FE-013)

| Requirement ID | Specification | Status | Implementation Details & Files | Contracts & Blockers |
|---|---|---|---|---|
| **FE-011** | Processing Pipeline Dispatcher | ✅ Implemented | Replaced invalid processor types in `src/components/evidence/processing-trigger-form.tsx` with exact 4 supported types (`document_ocr`, `speech_transcription`, `language_normalization`, `candidate_extraction`). Added `source_processing_run_id` UUID input and prerequisite rules. | `ProcessorType`, `TriggerProcessingRequest`; BG-006 |
| **FE-012** | Asynchronous Task Ledger | ✅ Implemented | Enhanced `src/components/evidence/task-status-panel.tsx`. Displays contract task table (`task_id`, `task_type`, `entity_id`, status badge, timestamps) without fake progress bars or percentages. Included exact state descriptions. | `AsyncTaskResponse`, `TaskStatus`; BG-006 |
| **FE-013** | Candidate Extraction Inspector | ✅ Implemented | Created `src/components/evidence/extraction-display.tsx`. Displays extracted entities, normalization, verification status badges, provenance links, and labels `null` confidence strictly as "Unknown". Documented demo extraction scope. | `ExtractedField`, `VerificationStatus`; BG-006, BG-007, BG-009 |

---

### Phase 4: Clinical Intelligence Workspace (FE-014 – FE-017)

| Requirement ID | Specification | Status | Implementation Details & Files | Contracts & Blockers |
|---|---|---|---|---|
| **FE-014** | Chronological Timeline & Conflicts | ✅ Implemented | Updated `src/components/intelligence/timeline-list.tsx` (all contract columns, precision badges, UNKNOWN temporal unanchored rule). Fixed misleading empty state in `src/components/intelligence/conflict-list.tsx` to "Conflicts Not Yet Evaluated". | `TimelineEvent`, `ClinicalConflict`; BG-006, BG-007, DEC-05 |
| **FE-015** | Missing Information & Clarifications | ✅ Implemented | Fixed misleading empty state in `src/components/intelligence/missing-info-list.tsx` to "Missing Information Not Yet Evaluated". Grouped categories, bounded questions to demo rules (max 3/round, 2 rounds), and labeled inquiries as display-only. | `MissingInfoItem`, `MissingInfoCategory`; BG-008 |
| **FE-016** | Trusted Guideline Retrieval Query | ✅ Implemented | Enhanced `src/components/intelligence/retrieval-form.tsx`. Strict integer validation for `corpus_version` (1–100) and `top_k` (1–50), query limit (1–4000), search mode enum (`hybrid`, `vector`, `keyword`), and relevance scoring disclaimer. | `RetrievalRequest`, `SearchMode`; BG-019 |
| **FE-017** | AI Advisory Draft Generation | ✅ Implemented | Enhanced `src/components/intelligence/ai-draft-form.tsx` and created case route `/cases/[id]/intelligence/page.tsx`. Added non-diagnostic safety badges, validator and human review badges, rejected draft quarantine block, and limitations display. Fixed global subtitle in `src/app/(shell)/intelligence/page.tsx`. | `AIDraftResponse`, `ValidatorStatus`; BG-010, BG-017 |
| **FE-029** | Classical Clinical Typography | ✅ Maintained | Times New Roman (`--font-serif`) preserved globally across text, headers, badges, forms, JSON, and UUID identifiers. | Design System Standard |

---

## 3. Verified Route Inventory

| Route | Implementation State | Associated Requirement |
|---|---|---|
| `/` → `/login` | ✅ Working Redirect | Root Authentication Gate |
| `/login` | ✅ Working | Form validation, disconnected notice |
| `/login/forgot-password` | ✅ Working | Recovery unavailable notice |
| `/cases` | ✅ Complete | Contract columns (`case_id`, `synthetic_subject_id`, `state`, `version`, `created_at`) + Exact UUID Lookup |
| `/cases/new` | ✅ Complete | Pure `CreateCaseRequest` UUID form, zero patient demographics |
| `/cases/[id]` | ✅ Complete | Resolves dynamic `params.id`, schema overview, sub-route navigation |
| `/cases/[id]/consent` | ✅ Complete (New) | 3 purpose cards, v1.0 notice, lifecycle states, BG-003 disclosure |
| `/cases/[id]/intake` | ✅ Complete (New) | Encounter form, encounter ledger, 20k char narrative intake |
| `/cases/[id]/evidence` | ✅ Complete (New) | Upload envelopes, NoOpScanner pipeline, 12-field evidence ledger, preview panel |
| `/cases/[id]/intelligence`| ✅ Complete (New) | Scoped intelligence workspace: timeline, conflicts, missing info, retrieval, AI drafts |
| `/evidence` | ✅ Complete | Global processing hub, processor dispatch, task status, extraction ledger |
| `/intelligence` | ✅ Complete | Global intelligence hub with Case UUID scoping selector and honest subtitle |
| `/design-system` | ✅ Preserved | Color tokens, typography, Base UI primitives catalog |
