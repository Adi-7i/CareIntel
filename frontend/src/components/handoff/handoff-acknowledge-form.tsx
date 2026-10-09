"use client";

import * as React from "react";
import { CheckSquare, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function HandoffAcknowledgeForm() {
  const [handoffId, setHandoffId] = React.useState("");
  const [reference, setReference] = React.useState("");
  const [expectedVersion, setExpectedVersion] = React.useState("1");
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!handoffId.trim()) newErrors.handoffId = "Handoff ID is required.";
    if (!reference.trim()) newErrors.reference = "Reference string is required.";
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
    setTimeout(() => setStatus("unconnected"), 800);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="haHandoffId" className={errors.handoffId ? "text-destructive" : ""}>Handoff ID *</Label>
        <Input id="haHandoffId" value={handoffId} onChange={(e) => { setHandoffId(e.target.value); if (errors.handoffId) setErrors({ ...errors, handoffId: "" }); }} disabled={status === "submitting"} className="max-w-md" />
        {errors.handoffId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.handoffId}</p>}
      </div>
      <div className="space-y-2 max-w-xl">
        <Label htmlFor="haRef" className={errors.reference ? "text-destructive" : ""}>Acknowledgement Reference *</Label>
        <Input id="haRef" value={reference} onChange={(e) => { setReference(e.target.value); if (errors.reference) setErrors({ ...errors, reference: "" }); }} disabled={status === "submitting"} placeholder="e.g. REC-9942" />
        {errors.reference && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.reference}</p>}
      </div>
      <div className="space-y-2 max-w-[200px]">
        <Label htmlFor="haVersion" className={errors.expectedVersion ? "text-destructive" : ""}>Expected Version *</Label>
        <Input id="haVersion" type="number" min="1" value={expectedVersion} onChange={(e) => { setExpectedVersion(e.target.value); if (errors.expectedVersion) setErrors({ ...errors, expectedVersion: "" }); }} disabled={status === "submitting"} />
        {errors.expectedVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedVersion}</p>}
      </div>
      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-xl">
          Validated locally. Requires backend integration.
        </p>
      )}
      <Button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Acknowledging..." : <><CheckSquare className="mr-2 size-4" />Acknowledge Handoff</>}
      </Button>
    </form>
  );
}
