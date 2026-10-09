"use client";

import * as React from "react";
import { Play, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function EvaluationTrigger() {
  const [caseId, setCaseId] = React.useState("");
  const [extractionRunId, setExtractionRunId] = React.useState("");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
    if (!extractionRunId.trim()) newErrors.extractionRunId = "Extraction Run ID is required.";
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

    // Simulate validation and immediate unconnected state
    setTimeout(() => {
      setStatus("unconnected");
    }, 800);
  };

  return (
    <div className="space-y-6">
      {status === "unconnected" && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4">
          <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold mb-1">
            Authentication & Persistence Disconnected
          </p>
          <p className="font-serif text-sm text-[var(--status-info-text)]">
            Trigger request validated locally. Execution requires a valid extraction run ID and backend integration.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="Evaluation trigger form">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="evalCaseId" className={errors.caseId ? "text-destructive" : ""}>Target Case ID *</Label>
            <Input
              id="evalCaseId"
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
            <Label htmlFor="extractionRunId" className={errors.extractionRunId ? "text-destructive" : ""}>Extraction Run ID *</Label>
            <Input
              id="extractionRunId"
              value={extractionRunId}
              onChange={(e) => {
                setExtractionRunId(e.target.value);
                if (errors.extractionRunId) setErrors({ ...errors, extractionRunId: "" });
              }}
              disabled={status === "submitting"}
              aria-invalid={!!errors.extractionRunId}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
            />
            {errors.extractionRunId && (
              <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.extractionRunId}
              </p>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? "Validating..." : (
              <>
                <Play className="mr-2 size-4" />
                Run Clinical Structuring
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
