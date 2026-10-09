"use client";

import * as React from "react";
import { PackageCheck, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ReferralFinalizeForm() {
  const [packageId, setPackageId] = React.useState("");
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!packageId.trim()) newErrors.packageId = "Package ID is required.";
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
        <Label htmlFor="rfPkgId" className={errors.packageId ? "text-destructive" : ""}>Referral Package ID *</Label>
        <Input id="rfPkgId" value={packageId} onChange={(e) => { setPackageId(e.target.value); if (errors.packageId) setErrors({ ...errors, packageId: "" }); }} disabled={status === "submitting"} className="max-w-md" />
        {errors.packageId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.packageId}</p>}
      </div>
      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-md">
          Validated locally. Requires backend integration.
        </p>
      )}
      <Button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Finalizing..." : <><PackageCheck className="mr-2 size-4" />Finalize Package</>}
      </Button>
    </form>
  );
}
