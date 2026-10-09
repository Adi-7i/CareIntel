"use client";

import * as React from "react";
import { Play, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "cn";

export function ProcessingTriggerForm() {
  const [evidenceId, setEvidenceId] = React.useState("");
  const [processorType, setProcessorType] = React.useState("");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!evidenceId.trim()) newErrors.evidenceId = "Evidence ID is required.";
    if (!processorType) newErrors.processorType = "Processor type must be selected.";
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

    // Simulate validation and immediate unconnected state
    setTimeout(() => {
      setStatus("unconnected");
    }, 800);
  };

  return (
    <div className="space-y-6">
      {status === "unconnected" && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4">
          <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold mb-1">
            Authentication & Persistence Disconnected
          </p>
          <p className="font-serif text-sm text-[var(--status-info-text)]">
            Trigger request validated locally. Actual execution requires a valid evidence ID and backend integration.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="Processing trigger form">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="targetEvidenceId" className={errors.evidenceId ? "text-destructive" : ""}>Target Evidence ID *</Label>
            <Input
              id="targetEvidenceId"
              value={evidenceId}
              onChange={(e) => {
                setEvidenceId(e.target.value);
                if (errors.evidenceId) setErrors({ ...errors, evidenceId: "" });
              }}
              disabled={status === "submitting"}
              aria-invalid={!!errors.evidenceId}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
            />
            {errors.evidenceId && (
              <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.evidenceId}
              </p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="processorType" className={errors.processorType ? "text-destructive" : ""}>Processor Type *</Label>
            <Select
              value={processorType}
              onValueChange={(val) => {
                setProcessorType(val || "");
                if (errors.processorType) setErrors({ ...errors, processorType: "" });
              }}
              disabled={status === "submitting"}
            >
              <SelectTrigger id="processorType" className={cn(errors.processorType && "border-destructive focus-visible:ring-destructive/50")}>
                <SelectValue placeholder="Select processor" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="document_ocr">Document OCR</SelectItem>
                <SelectItem value="speech_transcription">Speech Transcription</SelectItem>
                <SelectItem value="structure_extraction">Structure Extraction</SelectItem>
                <SelectItem value="clinical_intelligence">Clinical Intelligence</SelectItem>
              </SelectContent>
            </Select>
            {errors.processorType && (
              <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.processorType}
              </p>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? "Validating..." : (
              <>
                <Play className="mr-2 size-4" />
                Trigger Processing
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
