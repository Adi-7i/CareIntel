"use client";

import * as React from "react";
import { CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function HandoffCompleteForm() {
  const [handoffId, setHandoffId] = React.useState("");
  const [expectedHandoffVersion, setExpectedHandoffVersion] = React.useState("1");
  const [expectedCaseVersion, setExpectedCaseVersion] = React.useState("1");
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!handoffId.trim()) newErrors.handoffId = "Handoff ID is required.";
    const vH = parseInt(expectedHandoffVersion, 10);
    const vC = parseInt(expectedCaseVersion, 10);
    if (isNaN(vH) || vH < 1) newErrors.expectedHandoffVersion = "Must be >= 1.";
    if (isNaN(vC) || vC < 1) newErrors.expectedCaseVersion = "Must be >= 1.";
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
    setTimeout(() => setStatus("unconnected"), 800);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="hcHandoffId" className={errors.handoffId ? "text-destructive" : ""}>Handoff ID *</Label>
        <Input id="hcHandoffId" value={handoffId} onChange={(e) => { setHandoffId(e.target.value); if (errors.handoffId) setErrors({ ...errors, handoffId: "" }); }} disabled={status === "submitting"} className="max-w-md" />
        {errors.handoffId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.handoffId}</p>}
      </div>
      <div className="grid sm:grid-cols-2 gap-4 max-w-xl">
        <div className="space-y-2">
          <Label htmlFor="hcHandVer" className={errors.expectedHandoffVersion ? "text-destructive" : ""}>Expected Handoff Ver. *</Label>
          <Input id="hcHandVer" type="number" min="1" value={expectedHandoffVersion} onChange={(e) => { setExpectedHandoffVersion(e.target.value); if (errors.expectedHandoffVersion) setErrors({ ...errors, expectedHandoffVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedHandoffVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedHandoffVersion}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="hcCaseVer" className={errors.expectedCaseVersion ? "text-destructive" : ""}>Expected Case Ver. *</Label>
          <Input id="hcCaseVer" type="number" min="1" value={expectedCaseVersion} onChange={(e) => { setExpectedCaseVersion(e.target.value); if (errors.expectedCaseVersion) setErrors({ ...errors, expectedCaseVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedCaseVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedCaseVersion}</p>}
        </div>
      </div>
      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-xl">
          Validated locally. Requires backend integration.
        </p>
      )}
      <Button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Completing..." : <><CheckCircle2 className="mr-2 size-4" />Complete Handoff</>}
      </Button>
    </form>
  );
}
