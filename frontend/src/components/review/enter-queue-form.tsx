"use client";

import * as React from "react";
import { ArrowRight, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function EnterQueueForm() {
  const [caseId, setCaseId] = React.useState("");
  const [encounterId, setEncounterId] = React.useState("");
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
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
    <div className="space-y-6">
      {status === "unconnected" && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4">
          <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold mb-1">
            Authentication Disconnected
          </p>
          <p className="font-serif text-sm text-[var(--status-info-text)]">
            Case {caseId} validated locally. Submission to the review queue requires a connected backend session.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" aria-label="Enter queue form">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="eqCaseId" className={errors.caseId ? "text-destructive" : ""}>Target Case ID *</Label>
            <Input
              id="eqCaseId"
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
            <Label htmlFor="eqEncounterId">Encounter ID (Optional)</Label>
            <Input
              id="eqEncounterId"
              value={encounterId}
              onChange={(e) => setEncounterId(e.target.value)}
              disabled={status === "submitting"}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={status === "submitting"}>
            {status === "submitting" ? "Validating..." : (
              <>
                <ArrowRight className="mr-2 size-4" />
                Submit to Queue
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
