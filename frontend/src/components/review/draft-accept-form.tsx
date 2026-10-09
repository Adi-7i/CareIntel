"use client";

import * as React from "react";
import { Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function DraftAcceptForm() {
  const [draftId, setDraftId] = React.useState("");
  const [expectedDraftVersion, setExpectedDraftVersion] = React.useState("1");
  const [expectedQueueVersion, setExpectedQueueVersion] = React.useState("1");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!draftId.trim()) newErrors.draftId = "Draft ID is required.";
    const vD = parseInt(expectedDraftVersion, 10);
    const vQ = parseInt(expectedQueueVersion, 10);
    if (isNaN(vD) || vD < 1) newErrors.expectedDraftVersion = "Must be >= 1.";
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
    setTimeout(() => setStatus("unconnected"), 800);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="daDraftId" className={errors.draftId ? "text-destructive" : ""}>Draft ID *</Label>
        <Input id="daDraftId" value={draftId} onChange={(e) => { setDraftId(e.target.value); if (errors.draftId) setErrors({ ...errors, draftId: "" }); }} disabled={status === "submitting"} className="max-w-md" />
        {errors.draftId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.draftId}</p>}
      </div>
      <div className="grid sm:grid-cols-2 gap-4 max-w-md">
        <div className="space-y-2">
          <Label htmlFor="daDraftVer" className={errors.expectedDraftVersion ? "text-destructive" : ""}>Expected Draft Ver. *</Label>
          <Input id="daDraftVer" type="number" min="1" value={expectedDraftVersion} onChange={(e) => { setExpectedDraftVersion(e.target.value); if (errors.expectedDraftVersion) setErrors({ ...errors, expectedDraftVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedDraftVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedDraftVersion}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="daQueueVer" className={errors.expectedQueueVersion ? "text-destructive" : ""}>Expected Queue Ver. *</Label>
          <Input id="daQueueVer" type="number" min="1" value={expectedQueueVersion} onChange={(e) => { setExpectedQueueVersion(e.target.value); if (errors.expectedQueueVersion) setErrors({ ...errors, expectedQueueVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedQueueVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedQueueVersion}</p>}
        </div>
      </div>
      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-md">
          Validated locally. Requires backend integration.
        </p>
      )}
      <Button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Accepting..." : <><Check className="mr-2 size-4" />Accept Draft</>}
      </Button>
    </form>
  );
}
