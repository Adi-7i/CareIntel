"use client";

import * as React from "react";
import { CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "cn";

export function ReviewDecisionForm() {
  const [caseId, setCaseId] = React.useState("");
  const [draftId, setDraftId] = React.useState("");
  const [decisionType, setDecisionType] = React.useState("");
  const [rationale, setRationale] = React.useState("");
  const [expectedCaseVersion, setExpectedCaseVersion] = React.useState("1");
  const [expectedQueueVersion, setExpectedQueueVersion] = React.useState("1");
  const [expectedDraftVersion, setExpectedDraftVersion] = React.useState("1");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
    if (!draftId.trim()) newErrors.draftId = "Draft ID is required.";
    if (!decisionType) newErrors.decisionType = "Decision type is required.";
    
    const vC = parseInt(expectedCaseVersion, 10);
    const vQ = parseInt(expectedQueueVersion, 10);
    const vD = parseInt(expectedDraftVersion, 10);
    if (isNaN(vC) || vC < 1) newErrors.expectedCaseVersion = "Must be >= 1.";
    if (isNaN(vQ) || vQ < 1) newErrors.expectedQueueVersion = "Must be >= 1.";
    if (isNaN(vD) || vD < 1) newErrors.expectedDraftVersion = "Must be >= 1.";
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
    <form onSubmit={handleSubmit} className="space-y-4" aria-label="Review decision form">
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="rdCaseId" className={errors.caseId ? "text-destructive" : ""}>Case ID *</Label>
          <Input id="rdCaseId" value={caseId} onChange={(e) => { setCaseId(e.target.value); if (errors.caseId) setErrors({ ...errors, caseId: "" }); }} disabled={status === "submitting"} />
          {errors.caseId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.caseId}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="rdDraftId" className={errors.draftId ? "text-destructive" : ""}>Draft ID *</Label>
          <Input id="rdDraftId" value={draftId} onChange={(e) => { setDraftId(e.target.value); if (errors.draftId) setErrors({ ...errors, draftId: "" }); }} disabled={status === "submitting"} />
          {errors.draftId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.draftId}</p>}
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="decisionType" className={errors.decisionType ? "text-destructive" : ""}>Decision Type *</Label>
        <Select value={decisionType} onValueChange={(val) => { setDecisionType(val || ""); if (errors.decisionType) setErrors({ ...errors, decisionType: "" }); }} disabled={status === "submitting"}>
          <SelectTrigger id="decisionType" className={cn("w-full sm:max-w-md", errors.decisionType && "border-destructive focus-visible:ring-destructive/50")}>
            <SelectValue placeholder="Select verified decision type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="APPROVE">Approve</SelectItem>
            <SelectItem value="REJECT">Reject</SelectItem>
            <SelectItem value="REQUEST_CLARIFICATION">Request Clarification</SelectItem>
            <SelectItem value="ESCALATE">Escalate</SelectItem>
            <SelectItem value="REFER">Refer</SelectItem>
          </SelectContent>
        </Select>
        {errors.decisionType && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.decisionType}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="rdRationale">Rationale (Optional)</Label>
        <Textarea id="rdRationale" value={rationale} onChange={(e) => setRationale(e.target.value)} disabled={status === "submitting"} rows={3} maxLength={4000} placeholder="Required for some decisions by policy, but technically optional in schema." />
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="evC" className={errors.expectedCaseVersion ? "text-destructive" : ""}>Expected Case Ver. *</Label>
          <Input id="evC" type="number" min="1" value={expectedCaseVersion} onChange={(e) => { setExpectedCaseVersion(e.target.value); if (errors.expectedCaseVersion) setErrors({ ...errors, expectedCaseVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedCaseVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedCaseVersion}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="evQ" className={errors.expectedQueueVersion ? "text-destructive" : ""}>Expected Queue Ver. *</Label>
          <Input id="evQ" type="number" min="1" value={expectedQueueVersion} onChange={(e) => { setExpectedQueueVersion(e.target.value); if (errors.expectedQueueVersion) setErrors({ ...errors, expectedQueueVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedQueueVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedQueueVersion}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="evD" className={errors.expectedDraftVersion ? "text-destructive" : ""}>Expected Draft Ver. *</Label>
          <Input id="evD" type="number" min="1" value={expectedDraftVersion} onChange={(e) => { setExpectedDraftVersion(e.target.value); if (errors.expectedDraftVersion) setErrors({ ...errors, expectedDraftVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedDraftVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedDraftVersion}</p>}
        </div>
      </div>

      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded">
          Validated locally. Requires backend integration.
        </p>
      )}
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={status === "submitting"}>
          {status === "submitting" ? "Submitting..." : <><CheckCircle2 className="mr-2 size-4" />Submit Decision</>}
        </Button>
      </div>
    </form>
  );
}
