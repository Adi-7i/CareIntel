"use client";

import * as React from "react";
import { UserPlus, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function AssignReviewerForm() {
  const [caseId, setCaseId] = React.useState("");
  const [reviewerId, setReviewerId] = React.useState("");
  const [expectedVersion, setExpectedVersion] = React.useState("1");
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
    if (!reviewerId.trim()) newErrors.reviewerId = "Reviewer ID is required.";
    const v = parseInt(expectedVersion, 10);
    if (isNaN(v) || v < 1) newErrors.expectedVersion = "Must be >= 1.";
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
    <form onSubmit={handleSubmit} className="space-y-4" aria-label="Assign reviewer form">
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="arCaseId" className={errors.caseId ? "text-destructive" : ""}>Case ID *</Label>
          <Input id="arCaseId" value={caseId} onChange={(e) => { setCaseId(e.target.value); if (errors.caseId) setErrors({ ...errors, caseId: "" }); }} disabled={status === "submitting"} />
          {errors.caseId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.caseId}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="arReviewerId" className={errors.reviewerId ? "text-destructive" : ""}>Reviewer ID (UUID) *</Label>
          <Input id="arReviewerId" value={reviewerId} onChange={(e) => { setReviewerId(e.target.value); if (errors.reviewerId) setErrors({ ...errors, reviewerId: "" }); }} disabled={status === "submitting"} placeholder="UUID only. No user directory." />
          {errors.reviewerId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.reviewerId}</p>}
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="arVersion" className={errors.expectedVersion ? "text-destructive" : ""}>Expected Queue Version *</Label>
        <Input id="arVersion" type="number" min="1" value={expectedVersion} onChange={(e) => { setExpectedVersion(e.target.value); if (errors.expectedVersion) setErrors({ ...errors, expectedVersion: "" }); }} disabled={status === "submitting"} className="max-w-[200px]" />
        {errors.expectedVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedVersion}</p>}
      </div>
      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded">
          Validated locally. Requires backend integration.
        </p>
      )}
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={status === "submitting"}>
          {status === "submitting" ? "Assigning..." : <><UserPlus className="mr-2 size-4" />Assign Reviewer</>}
        </Button>
      </div>
    </form>
  );
}
