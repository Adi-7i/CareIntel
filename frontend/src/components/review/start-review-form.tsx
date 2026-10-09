"use client";

import * as React from "react";
import { PlayCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function StartReviewForm() {
  const [caseId, setCaseId] = React.useState("");
  const [expectedVersion, setExpectedVersion] = React.useState("1");
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
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
    <form onSubmit={handleSubmit} className="space-y-4" aria-label="Start review form">
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="srCaseId" className={errors.caseId ? "text-destructive" : ""}>Case ID *</Label>
          <Input id="srCaseId" value={caseId} onChange={(e) => { setCaseId(e.target.value); if (errors.caseId) setErrors({ ...errors, caseId: "" }); }} disabled={status === "submitting"} />
          {errors.caseId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.caseId}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="srVersion" className={errors.expectedVersion ? "text-destructive" : ""}>Expected Queue Version *</Label>
          <Input id="srVersion" type="number" min="1" value={expectedVersion} onChange={(e) => { setExpectedVersion(e.target.value); if (errors.expectedVersion) setErrors({ ...errors, expectedVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedVersion}</p>}
        </div>
      </div>
      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded">
          Validated locally. Requires backend integration.
        </p>
      )}
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={status === "submitting"}>
          {status === "submitting" ? "Starting..." : <><PlayCircle className="mr-2 size-4" />Start Review</>}
        </Button>
      </div>
    </form>
  );
}
