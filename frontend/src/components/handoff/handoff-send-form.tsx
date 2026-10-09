"use client";

import * as React from "react";
import { Send, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function HandoffSendForm() {
  const [handoffId, setHandoffId] = React.useState("");
  const [expectedVersion, setExpectedVersion] = React.useState("1");
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!handoffId.trim()) newErrors.handoffId = "Handoff ID is required.";
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
      <div className="grid sm:grid-cols-2 gap-4 max-w-xl">
        <div className="space-y-2">
          <Label htmlFor="hsHandoffId" className={errors.handoffId ? "text-destructive" : ""}>Handoff ID *</Label>
          <Input id="hsHandoffId" value={handoffId} onChange={(e) => { setHandoffId(e.target.value); if (errors.handoffId) setErrors({ ...errors, handoffId: "" }); }} disabled={status === "submitting"} />
          {errors.handoffId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.handoffId}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="hsVersion" className={errors.expectedVersion ? "text-destructive" : ""}>Expected Version *</Label>
          <Input id="hsVersion" type="number" min="1" value={expectedVersion} onChange={(e) => { setExpectedVersion(e.target.value); if (errors.expectedVersion) setErrors({ ...errors, expectedVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedVersion}</p>}
        </div>
      </div>
      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-xl">
          Validated locally. Requires backend integration.
        </p>
      )}
      <Button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Sending..." : <><Send className="mr-2 size-4" />Send Handoff</>}
      </Button>
    </form>
  );
}
