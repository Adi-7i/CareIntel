"use client";

import * as React from "react";
import { Sparkles, AlertCircle, FileText, ShieldAlert, CheckCircle2, ShieldCheck, AlertTriangle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { ValidatorStatus, HumanReviewStatus, AIDraftResponse } from "@/types";
import { cn } from "cn";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

interface AIDraftFormProps {
  caseId?: string;
  draft?: AIDraftResponse | null;
}

function ValidatorBadge({ status }: { status: ValidatorStatus }) {
  switch (status) {
    case "ACCEPTED":
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]">
          <CheckCircle2 className="mr-1 size-3" /> VALIDATOR: ACCEPTED
        </Badge>
      );
    case "REPAIR_ATTEMPTED":
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-warning-surface)] text-[var(--status-warning-text)] border-[var(--status-warning)]">
          <AlertTriangle className="mr-1 size-3" /> VALIDATOR: REPAIR ATTEMPTED
        </Badge>
      );
    case "REJECTED":
    default:
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]">
          <XCircle className="mr-1 size-3" /> VALIDATOR: REJECTED
        </Badge>
      );
  }
}

function HumanReviewBadge({ status }: { status: HumanReviewStatus }) {
  switch (status) {
    case "APPROVED":
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]">
          HUMAN REVIEW: APPROVED
        </Badge>
      );
    case "REJECTED":
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]">
          HUMAN REVIEW: REJECTED
        </Badge>
      );
    case "DRAFT":
    default:
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-slate-100 text-slate-700 border-slate-300">
          HUMAN REVIEW: PENDING DRAFT
        </Badge>
      );
  }
}

export function AIDraftForm({ caseId: initialCaseId = "", draft = null }: AIDraftFormProps) {
  const [caseId, setCaseId] = React.useState(initialCaseId);
  const [retrievalRunId, setRetrievalRunId] = React.useState("");
  const [taskType, setTaskType] = React.useState("");

  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [validatedData, setValidatedData] = React.useState<{
    case_id: string;
    retrieval_run_id: string;
    task_type: string;
  } | null>(null);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!caseId.trim()) {
      newErrors.caseId = "Target Case ID is required.";
    } else if (!UUID_REGEX.test(caseId.trim())) {
      newErrors.caseId = "Case ID must be a valid RFC 4122 UUID.";
    }

    if (!retrievalRunId.trim()) {
      newErrors.retrievalRunId = "Retrieval Run ID is required.";
    } else if (!UUID_REGEX.test(retrievalRunId.trim())) {
      newErrors.retrievalRunId = "Retrieval Run ID must be a valid RFC 4122 UUID.";
    }

    if (!taskType) newErrors.taskType = "Task type must be selected.";

    return newErrors;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (status === "submitting") return;

    const newErrors = validate();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setStatus("submitting");

    setValidatedData({
      case_id: caseId.trim(),
      retrieval_run_id: retrievalRunId.trim(),
      task_type: taskType,
    });

    setTimeout(() => {
      setStatus("unconnected");
    }, 400);
  };

  return (
    <div className="space-y-8">
      {/* Non-Diagnostic & Safety Mandate Banner */}
      <div className="rounded-md bg-slate-50 border border-slate-200 p-4 text-xs font-serif text-slate-700 space-y-1">
        <div className="flex items-center gap-2 font-semibold text-secondary">
          <ShieldAlert className="size-4 text-[var(--ci-teal-700)] shrink-0" />
          <span>Non-Authoritative Advisory Draft Architecture (FE-017, requirement.md §6)</span>
        </div>
        <p>
          AI-generated drafts are non-diagnostic, decision-support artifacts generated strictly for licensed clinician assessment. Generated outputs must <span className="underline font-semibold">never</span> be treated as final clinical triage without qualified human reviewer sign-off.
        </p>
      </div>

      {status === "unconnected" && validatedData && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-[var(--status-info-text)] shrink-0" />
            <p className="font-serif text-xs text-[var(--status-info-text)] font-semibold">
              AI Advisory Draft Request Validated Locally
            </p>
          </div>
          <p className="font-serif text-xs text-[var(--status-info-text)]">
            Generation envelope conforms to schema. Dispatch requires POST <code className="bg-white/60 px-1 py-0.5 rounded">/api/v1/cases/{caseId}/ai-draft</code>.
          </p>
          <div className="bg-white/80 p-2.5 rounded text-xs font-mono border overflow-x-auto text-slate-800">
            {JSON.stringify(validatedData, null, 2)}
          </div>
        </div>
      )}

      {/* Generation Trigger Form */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <Sparkles className="size-4 text-[var(--ci-teal-700)]" />
            Generate AI Advisory Draft (FE-017)
          </h2>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6" aria-label="AI draft form">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="aiCaseId" className={errors.caseId ? "text-destructive" : ""}>
                  Target Case ID *
                </Label>
                <Input
                  id="aiCaseId"
                  value={caseId}
                  onChange={(e) => {
                    setCaseId(e.target.value);
                    if (errors.caseId) setErrors((prev) => ({ ...prev, caseId: "" }));
                  }}
                  disabled={status === "submitting" || Boolean(initialCaseId)}
                  aria-invalid={!!errors.caseId}
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                  className={errors.caseId ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
                />
                {errors.caseId && (
                  <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.caseId}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="retrievalRunId" className={errors.retrievalRunId ? "text-destructive" : ""}>
                  Retrieval Run ID *
                </Label>
                <Input
                  id="retrievalRunId"
                  value={retrievalRunId}
                  onChange={(e) => {
                    setRetrievalRunId(e.target.value);
                    if (errors.retrievalRunId) setErrors((prev) => ({ ...prev, retrievalRunId: "" }));
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.retrievalRunId}
                  placeholder="UUID of completed retrieval run"
                  className={errors.retrievalRunId ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
                />
                <p className="text-[11px] text-muted-foreground font-serif">
                  Grounding requirement: drafts must be grounded in an authorized retrieval run.
                </p>
                {errors.retrievalRunId && (
                  <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.retrievalRunId}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="taskType" className={errors.taskType ? "text-destructive" : ""}>
                Advisory Task Type *
              </Label>
              <Select
                value={taskType}
                onValueChange={(val) => {
                  setTaskType(val || "");
                  if (errors.taskType) setErrors((prev) => ({ ...prev, taskType: "" }));
                }}
                disabled={status === "submitting"}
              >
                <SelectTrigger id="taskType" className={cn("font-serif text-xs", errors.taskType && "border-destructive focus-visible:ring-destructive/50")}>
                  <SelectValue placeholder="Select advisory task" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="reviewer_note_draft">Reviewer Note Draft (Synthesized Clinical Impression)</SelectItem>
                  <SelectItem value="evidence_summary">Evidence Summary (Chronological Extraction Digest)</SelectItem>
                  <SelectItem value="structured_case_summary">Structured Case Summary (Intake Dossier)</SelectItem>
                  <SelectItem value="clarification_support">Clarification Support (Question Formulation)</SelectItem>
                </SelectContent>
              </Select>
              {errors.taskType && (
                <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" /> {errors.taskType}
                </p>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" size="sm" disabled={status === "submitting"} aria-busy={status === "submitting"}>
                {status === "submitting" ? (
                  "Validating..."
                ) : (
                  <>
                    <Sparkles className="mr-1.5 size-3.5" />
                    Dispatch Draft Generation
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>

      {/* Results Display Panel */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <FileText className="size-4 text-[var(--ci-teal-700)]" />
            <h2 className="font-serif font-semibold text-secondary text-sm">
              AI Advisory Draft Artifact
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-serif text-xs bg-amber-50 text-amber-900 border-amber-300">
              Not Clinically Authoritative
            </Badge>
          </div>
        </div>

        <div className="p-6">
          {!draft ? (
            <EmptyState
              icon={<Sparkles className="size-8 text-muted-foreground" />}
              title="No Draft Artifact Generated"
              description="Dispatch an AI advisory task above to produce an evaluation draft for qualified clinician review."
            />
          ) : (
            <div className="space-y-6">
              {/* Badges Bar */}
              <div className="flex flex-wrap items-center gap-2 border-b pb-4">
                <ValidatorBadge status={draft.validator_status} />
                <HumanReviewBadge status={draft.review_status} />
                <span className="text-xs font-mono text-muted-foreground ml-auto">
                  Model: {draft.model_identifier} • Generated: {draft.generated_at}
                </span>
              </div>

              {/* Quarantine Block if Rejected */}
              {draft.validator_status === "REJECTED" && (
                <div className="rounded-md bg-red-50 border border-red-300 p-4 text-xs font-serif text-red-900 space-y-1">
                  <div className="flex items-center gap-2 font-semibold">
                    <ShieldAlert className="size-4 text-red-700 shrink-0" />
                    <span>Quarantined Draft Artifact (Automated Validator Rejection)</span>
                  </div>
                  <p>
                    This draft failed automated clinical safety and consistency validations. It is isolated from referral and triage workflows. Review is restricted to supervisory quality evaluation.
                  </p>
                </div>
              )}

              {/* Draft Content */}
              <div className="space-y-4 font-serif">
                <div className="space-y-1">
                  <h3 className="font-semibold text-secondary text-sm">Triage Recommendation (Advisory Only)</h3>
                  <p className="text-slate-800 text-sm leading-relaxed p-3 bg-slate-50/50 rounded border">
                    {draft.triage_recommendation}
                  </p>
                </div>

                <div className="space-y-1">
                  <h3 className="font-semibold text-secondary text-sm">Synthesized Clinical Summary</h3>
                  <p className="text-slate-800 text-sm leading-relaxed p-3 bg-slate-50/50 rounded border">
                    {draft.clinical_summary}
                  </p>
                </div>
              </div>

              {/* Limitations Section */}
              {draft.limitations && draft.limitations.length > 0 && (
                <div className="border-t pt-4 space-y-2">
                  <h4 className="font-serif font-semibold text-secondary text-xs uppercase tracking-wider">
                    Model Uncertainty & Data Limitations
                  </h4>
                  <ul className="list-disc pl-5 text-xs font-serif text-muted-foreground space-y-1">
                    {draft.limitations.map((lim, idx) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
