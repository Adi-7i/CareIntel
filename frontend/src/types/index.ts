/**
 * CareIntel Domain Types
 * Derived strictly from backend contracts verified in requirement.md §6 & §16.
 * All clinical, case, consent, evidence, processing, and intelligence types.
 */

// ==========================================
// Identifiers & Common Types
// ==========================================

export type UUID = string;

// ==========================================
// Case & Subject Types (FE-003, FE-004)
// ==========================================

export type CaseState =
  | "CREATED"
  | "CONSENTED"
  | "INPUT_RECEIVED"
  | "PROCESSING"
  | "EXTRACTING"
  | "NORMALIZING"
  | "RETRIEVING"
  | "AI_ANALYSIS"
  | "SAFETY_CHECK"
  | "TRIAGE_DRAFT_READY"
  | "REVIEW_PENDING"
  | "REVIEWED"
  | "ESCALATED"
  | "REFERRED"
  | "COMPLETED"
  | "FAILED";

export interface CreateCaseRequest {
  synthetic_subject_id: UUID;
  facility_id?: UUID;
  consent_id: UUID;
}

export interface CaseResponse {
  case_id: UUID;
  synthetic_subject_id: UUID;
  facility_id?: UUID;
  state: CaseState;
  version: number;
  opened_by: UUID;
  assigned_to?: UUID;
  created_at: string;
  updated_at: string;
}

// ==========================================
// Consent Types (FE-006)
// ==========================================

export type ConsentState = "REQUESTED" | "ACTIVE" | "WITHDRAWN";

export type ConsentPurpose = "data_processing" | "ai_analysis" | "referral";

export interface CreateConsentRequest {
  subject_id: UUID;
  purpose: ConsentPurpose;
  notice_version: string; // e.g. "1.0"
}

export interface ConsentResponse {
  consent_id: UUID;
  subject_id: UUID;
  purpose: ConsentPurpose;
  notice_version: string;
  state: ConsentState;
  created_at?: string;
  updated_at?: string;
}

// ==========================================
// Encounter & Narrative Types (FE-005, FE-007)
// ==========================================

export interface CreateEncounterRequest {
  case_id: UUID;
  encounter_type: string; // 1-100 characters
  occurred_at: string; // ISO 8601 with timezone
  notes?: string; // <= 2000 characters
}

export interface EncounterResponse {
  encounter_id: UUID;
  case_id: UUID;
  encounter_type: string;
  occurred_at: string;
  notes?: string;
  created_at?: string;
}

export interface NarrativeIntakeRequest {
  case_id: UUID;
  encounter_id?: UUID;
  text: string; // <= 20000 characters
  source_language?: string; // BCP-47 tag, e.g. "en", "hi-Latn"
}

// ==========================================
// Evidence Types (FE-008, FE-009, FE-010)
// ==========================================

export type EvidenceModality = "text" | "document" | "image" | "audio";

export type EvidenceState = "PENDING_UPLOAD" | "STORED" | "READY" | "QUARANTINED" | "FAILED";

export interface EvidenceResponse {
  evidence_id: UUID;
  case_id: UUID;
  encounter_id?: UUID;
  modality: EvidenceModality;
  state: EvidenceState;
  content_type: string;
  size_bytes: number;
  original_filename: string;
  source_language?: string;
  created_by: UUID;
  created_at: string;
  provenance: string;
}

export interface CreateEvidenceRequest {
  case_id: UUID;
  encounter_id?: UUID;
  modality: EvidenceModality;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  source_language?: string;
}

// ==========================================
// Processing & Tasks (FE-011, FE-012, FE-013)
// ==========================================

export type ProcessorType =
  | "document_ocr"
  | "speech_transcription"
  | "language_normalization"
  | "candidate_extraction";

export type ProcessingStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface TriggerProcessingRequest {
  evidence_id: UUID;
  processor_type: ProcessorType;
  source_processing_run_id?: UUID; // Required for language_normalization and candidate_extraction
}

export interface ProcessingRunResponse {
  run_id: UUID;
  evidence_id: UUID;
  processor_type: ProcessorType;
  status: ProcessingStatus;
  provider?: string;
  config_version?: string;
  started_at?: string;
  completed_at?: string;
  failure_reason?: string;
}

export type TaskStatus = "PENDING" | "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED";

export interface AsyncTaskResponse {
  task_id: UUID;
  task_type: string;
  entity_id: UUID;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export type VerificationStatus = "UNVERIFIED" | "VERIFIED" | "REJECTED";

export interface ExtractedField {
  field_id: string;
  field_type: string; // e.g. "symptom", "temporal", "demographic_synthetic"
  raw_value: string;
  normalized_value?: string;
  confidence: number | null; // null if unknown/uncalibrated
  verification_status: VerificationStatus;
  provenance_evidence_id: UUID;
  run_id?: UUID;
}

// ==========================================
// Clinical Intelligence (FE-014, FE-015, FE-016, FE-017)
// ==========================================

export type TemporalPrecision = "EXACT" | "DATE_ONLY" | "APPROXIMATE" | "UNKNOWN";

export interface TimelineEvent {
  event_id: string;
  source_statement: string;
  event_type: string;
  raw_temporal_expression?: string;
  precision: TemporalPrecision;
  resolution?: string;
  normalized_date_bounds?: {
    start?: string;
    end?: string;
  };
  unresolved_reason?: string;
  status: "NORMALIZED" | "UNRESOLVED" | "DISPUTED";
}

export type ConflictStatus = "UNRESOLVED" | "RESOLVED" | "DISMISSED";

export interface ClinicalConflict {
  conflict_id: string;
  field_name: string;
  status: ConflictStatus;
  detection_run_id?: UUID;
  conflicting_evidence_ids: UUID[];
  description: string;
  detected_at?: string;
}

export type MissingInfoCategory = "MISSING" | "CONFLICTING" | "UNREADABLE" | "UNVERIFIED" | "SATISFIED";

export interface MissingInfoItem {
  item_id: string;
  category: MissingInfoCategory;
  question_prompt: string;
  clinical_rationale: string;
  round_number: number; // 1..2
  is_blocking: boolean;
}

export type SearchMode = "vector" | "keyword" | "hybrid";

export interface RetrievalRequest {
  query: string; // 1-4000 chars
  corpus_version: number; // integer 1-100
  top_k: number; // integer 1-50, default 10
  search_mode: SearchMode;
}

export interface RetrievalResultItem {
  document_id: string;
  title: string;
  score: number; // Search relevance score, not clinical confidence
  snippet?: string;
  published_date?: string;
}

export interface RetrievalResponse {
  query: string;
  corpus_version: number;
  search_mode: SearchMode;
  results: RetrievalResultItem[];
}

export type ValidatorStatus = "ACCEPTED" | "REJECTED" | "REPAIR_ATTEMPTED";
export type HumanReviewStatus = "DRAFT" | "APPROVED" | "REJECTED";

export interface AIDraftResponse {
  draft_id: UUID;
  case_id: UUID;
  triage_recommendation: string;
  clinical_summary: string;
  validator_status: ValidatorStatus;
  review_status: HumanReviewStatus;
  limitations: string[];
  generated_at: string;
  model_identifier: string;
}
