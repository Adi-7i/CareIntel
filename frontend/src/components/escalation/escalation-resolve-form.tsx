"use client";

import * as React from "react";
import { CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function EscalationResolveForm() {
  const [escalationId, setEscalationId] = React.useState("");
  const [resolutionNotes, setResolutionNotes] = React.useState("");
  const [expectedCaseVersion, setExpectedCaseVersion] = React.useState("1");
  const [expectedQueueVersion, setExpectedQueueVersion] = React.useState("1");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!escalationId.trim()) newErrors.escalationId = "Escalation ID is required.";
    if (!resolutionNotes.trim()) newErrors.resolutionNotes = "Resolution notes are required.";
    
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
    <form onSubmit={handleSubmit} className="space-y-4" aria-label="Resolve escalation form">
      <div className="space-y-2">
        <Label htmlFor="resEscId" className={errors.escalationId ? "text-destructive" : ""}>Escalation ID *</Label>
        <Input id="resEscId" value={escalationId} onChange={(e) => { setEscalationId(e.target.value); if (errors.escalationId) setErrors({ ...errors, escalationId: "" }); }} disabled={status === "submitting"} className="max-w-md" />
        {errors.escalationId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.escalationId}</p>}
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="resNotes" className={errors.resolutionNotes ? "text-destructive" : ""}>Resolution Notes *</Label>
        <Textarea id="resNotes" value={resolutionNotes} onChange={(e) => { setResolutionNotes(e.target.value); if (errors.resolutionNotes) setErrors({ ...errors, resolutionNotes: "" }); }} disabled={status === "submitting"} rows={4} maxLength={4000} placeholder="Provide notes detailing the resolution..." />
        {errors.resolutionNotes && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.resolutionNotes}</p>}
      </div>

      <div className="grid sm:grid-cols-2 gap-4 max-w-md">
        <div className="space-y-2">
          <Label htmlFor="resEvC" className={errors.expectedCaseVersion ? "text-destructive" : ""}>Expected Case Ver. *</Label>
          <Input id="resEvC" type="number" min="1" value={expectedCaseVersion} onChange={(e) => { setExpectedCaseVersion(e.target.value); if (errors.expectedCaseVersion) setErrors({ ...errors, expectedCaseVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedCaseVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedCaseVersion}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="resEvQ" className={errors.expectedQueueVersion ? "text-destructive" : ""}>Expected Queue Ver. *</Label>
          <Input id="resEvQ" type="number" min="1" value={expectedQueueVersion} onChange={(e) => { setExpectedQueueVersion(e.target.value); if (errors.expectedQueueVersion) setErrors({ ...errors, expectedQueueVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedQueueVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedQueueVersion}</p>}
        </div>
      </div>

      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-md">
          Validated locally. Requires backend integration.
        </p>
      )}
      <div className="flex justify-start pt-2">
        <Button type="submit" disabled={status === "submitting"}>
          {status === "submitting" ? "Resolving..." : <><CheckCircle className="mr-2 size-4" />Resolve Escalation</>}
        </Button>
      </div>
    </form>
  );
}
