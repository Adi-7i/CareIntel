"use client";

import * as React from "react";
import { PackagePlus, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ReferralPrepareForm() {
  const [caseId, setCaseId] = React.useState("");
  const [evidenceIds, setEvidenceIds] = React.useState("");
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
    const ids = evidenceIds.split(",").map(i => i.trim()).filter(Boolean);
    if (ids.length === 0) newErrors.evidenceIds = "At least one Evidence ID is required.";
    else if (ids.length > 100) newErrors.evidenceIds = "Maximum 100 Evidence IDs allowed.";
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
        <Label htmlFor="rpCaseId" className={errors.caseId ? "text-destructive" : ""}>Case ID *</Label>
        <Input id="rpCaseId" value={caseId} onChange={(e) => { setCaseId(e.target.value); if (errors.caseId) setErrors({ ...errors, caseId: "" }); }} disabled={status === "submitting"} className="max-w-md" />
        {errors.caseId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.caseId}</p>}
      </div>
      <div className="space-y-2 max-w-xl">
        <Label htmlFor="rpEvIds" className={errors.evidenceIds ? "text-destructive" : ""}>Evidence IDs (Comma separated UUIDs) *</Label>
        <Input id="rpEvIds" value={evidenceIds} onChange={(e) => { setEvidenceIds(e.target.value); if (errors.evidenceIds) setErrors({ ...errors, evidenceIds: "" }); }} disabled={status === "submitting"} placeholder="uuid1, uuid2..." />
        {errors.evidenceIds && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.evidenceIds}</p>}
      </div>
      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-md">
          Validated locally. Requires backend integration.
        </p>
      )}
      <Button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Preparing..." : <><PackagePlus className="mr-2 size-4" />Prepare Referral Package</>}
      </Button>
    </form>
  );
}
