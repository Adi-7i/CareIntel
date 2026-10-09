"use client";

import * as React from "react";
import { Sparkles, AlertCircle, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "cn";

export function AIDraftForm() {
  const [caseId, setCaseId] = React.useState("");
  const [retrievalRunId, setRetrievalRunId] = React.useState("");
  const [taskType, setTaskType] = React.useState("");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
    if (!retrievalRunId.trim()) newErrors.retrievalRunId = "Retrieval Run ID is required.";
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

    setTimeout(() => {
      setStatus("unconnected");
    }, 800);
  };

  return (
    <div className="space-y-8">
      {status === "unconnected" && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4">
          <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold mb-1">
            Authentication Disconnected
          </p>
          <p className="font-serif text-sm text-[var(--status-info-text)]">
            AI Draft trigger validated locally. Actual generation requires backend integration and valid inputs.
          </p>
        </div>
      )}

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <Sparkles className="size-4" />
            Generate AI Advisory Draft
          </h2>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6" aria-label="AI draft form">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="aiCaseId" className={errors.caseId ? "text-destructive" : ""}>Target Case ID *</Label>
                <Input
                  id="aiCaseId"
                  value={caseId}
                  onChange={(e) => {
                    setCaseId(e.target.value);
                    if (errors.caseId) setErrors({ ...errors, caseId: "" });
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.caseId}
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                />
                {errors.caseId && (
                  <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.caseId}
                  </p>
                )}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="retrievalRunId" className={errors.retrievalRunId ? "text-destructive" : ""}>Retrieval Run ID *</Label>
                <Input
                  id="retrievalRunId"
                  value={retrievalRunId}
                  onChange={(e) => {
                    setRetrievalRunId(e.target.value);
                    if (errors.retrievalRunId) setErrors({ ...errors, retrievalRunId: "" });
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.retrievalRunId}
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                />
                {errors.retrievalRunId && (
                  <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.retrievalRunId}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="taskType" className={errors.taskType ? "text-destructive" : ""}>Task Type *</Label>
              <Select
                value={taskType}
                onValueChange={(val) => {
                  setTaskType(val || "");
                  if (errors.taskType) setErrors({ ...errors, taskType: "" });
                }}
                disabled={status === "submitting"}
              >
                <SelectTrigger id="taskType" className={cn("max-w-md", errors.taskType && "border-destructive focus-visible:ring-destructive/50")}>
                  <SelectValue placeholder="Select advisory task" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="reviewer_note_draft">Reviewer Note Draft</SelectItem>
                  <SelectItem value="evidence_summary">Evidence Summary</SelectItem>
                  <SelectItem value="structured_case_summary">Structured Case Summary</SelectItem>
                  <SelectItem value="clarification_support">Clarification Support</SelectItem>
                </SelectContent>
              </Select>
              {errors.taskType && (
                <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" /> {errors.taskType}
                </p>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={status === "submitting"} aria-busy={status === "submitting"}>
                {status === "submitting" ? "Generating..." : (
                  <>
                    <Sparkles className="mr-2 size-4" />
                    Generate Draft
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>

      <div className="border rounded-lg bg-[var(--status-warning-surface)] shadow-sm overflow-hidden border-[var(--status-warning)]">
        <div className="bg-[var(--status-warning)]/10 px-6 py-4 border-b border-[var(--status-warning)]/30 flex justify-between items-center">
          <h2 className="font-serif font-semibold text-[var(--status-warning-text)] flex items-center gap-2">
            <FileText className="size-4" />
            AI-Generated Draft Results
          </h2>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--status-warning-text)] border border-[var(--status-warning)]/50 px-2 py-0.5 rounded-full">
            Unverified
          </span>
        </div>
        <div className="p-6">
          <p className="font-serif text-sm text-[var(--status-warning-text)] mb-6">
            <strong>Warning:</strong> Any content displayed here is an AI-generated draft and is not a confirmed clinical finding.
          </p>
          <EmptyState
            icon={<Sparkles className="size-8" />}
            title="No Draft Available"
            description="Trigger an AI advisory task to view the draft content."
          />
        </div>
      </div>
    </div>
  );
}
