"use client";

import * as React from "react";
import { ArrowUpRight, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function EscalationForm() {
  const [caseId, setCaseId] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [expectedCaseVersion, setExpectedCaseVersion] = React.useState("1");
  const [expectedQueueVersion, setExpectedQueueVersion] = React.useState("1");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
    if (!reason.trim()) newErrors.reason = "Reason is required.";
    
    const vC = parseInt(expectedCaseVersion, 10);
    const vQ = parseInt(expectedQueueVersion, 10);
    if (isNaN(vC) || vC < 1) newErrors.expectedCaseVersion = "Must be >= 1.";
    if (isNaN(vQ) || vQ < 1) newErrors.expectedQueueVersion = "Must be >= 1.";
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
    <form onSubmit={handleSubmit} className="space-y-4" aria-label="Create escalation form">
      <div className="space-y-2">
        <Label htmlFor="escCaseId" className={errors.caseId ? "text-destructive" : ""}>Case ID *</Label>
        <Input id="escCaseId" value={caseId} onChange={(e) => { setCaseId(e.target.value); if (errors.caseId) setErrors({ ...errors, caseId: "" }); }} disabled={status === "submitting"} className="max-w-md" />
        {errors.caseId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.caseId}</p>}
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="escReason" className={errors.reason ? "text-destructive" : ""}>Escalation Reason *</Label>
        <Textarea id="escReason" value={reason} onChange={(e) => { setReason(e.target.value); if (errors.reason) setErrors({ ...errors, reason: "" }); }} disabled={status === "submitting"} rows={4} maxLength={4000} placeholder="Provide details for escalation..." />
        {errors.reason && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.reason}</p>}
      </div>

      <div className="grid sm:grid-cols-2 gap-4 max-w-md">
        <div className="space-y-2">
          <Label htmlFor="escEvC" className={errors.expectedCaseVersion ? "text-destructive" : ""}>Expected Case Ver. *</Label>
          <Input id="escEvC" type="number" min="1" value={expectedCaseVersion} onChange={(e) => { setExpectedCaseVersion(e.target.value); if (errors.expectedCaseVersion) setErrors({ ...errors, expectedCaseVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedCaseVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedCaseVersion}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="escEvQ" className={errors.expectedQueueVersion ? "text-destructive" : ""}>Expected Queue Ver. *</Label>
          <Input id="escEvQ" type="number" min="1" value={expectedQueueVersion} onChange={(e) => { setExpectedQueueVersion(e.target.value); if (errors.expectedQueueVersion) setErrors({ ...errors, expectedQueueVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedQueueVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedQueueVersion}</p>}
        </div>
      </div>

      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-md">
          Validated locally. Requires backend integration.
        </p>
      )}
      <div className="flex justify-start pt-2">
        <Button variant="destructive" type="submit" disabled={status === "submitting"}>
          {status === "submitting" ? "Escalating..." : <><ArrowUpRight className="mr-2 size-4" />Create Escalation</>}
        </Button>
      </div>
    </form>
  );
}
