"use client";

import * as React from "react";
import { Play, AlertCircle, Info, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { ProcessorType, TriggerProcessingRequest } from "@/types";
import { cn } from "cn";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const PROCESSOR_PREREQUISITES: Record<ProcessorType, { label: string; prereq: string; requiresSourceRun: boolean }> = {
  document_ocr: {
    label: "Document OCR (Optical Character Recognition)",
    prereq: "Requires evidence in READY state with modality 'document' or 'image'.",
    requiresSourceRun: false,
  },
  speech_transcription: {
    label: "Speech Transcription (ASR Engine)",
    prereq: "Requires evidence in READY state with modality 'audio'.",
    requiresSourceRun: false,
  },
  language_normalization: {
    label: "Language Normalization (Clinical Lexicon Normalizer)",
    prereq: "Requires a completed upstream run ID (OCR or Transcription output) via source_processing_run_id.",
    requiresSourceRun: true,
  },
  candidate_extraction: {
    label: "Candidate Extraction (Clinical Field Extraction)",
    prereq: "Requires a completed upstream normalization run ID via source_processing_run_id.",
    requiresSourceRun: true,
  },
};

export function ProcessingTriggerForm() {
  const [evidenceId, setEvidenceId] = React.useState("");
  const [processorType, setProcessorType] = React.useState<ProcessorType | "">("");
  const [sourceProcessingRunId, setSourceProcessingRunId] = React.useState("");

  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [validatedPayload, setValidatedPayload] = React.useState<TriggerProcessingRequest | null>(null);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const isSourceRunRequired = processorType ? PROCESSOR_PREREQUISITES[processorType]?.requiresSourceRun : false;

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!evidenceId.trim()) {
      newErrors.evidenceId = "Evidence ID is required.";
    } else if (!UUID_REGEX.test(evidenceId.trim())) {
      newErrors.evidenceId = "Evidence ID must be a valid RFC 4122 UUID.";
    }

    if (!processorType) {
      newErrors.processorType = "Processor type must be selected.";
    }

    if (isSourceRunRequired) {
      if (!sourceProcessingRunId.trim()) {
        newErrors.sourceProcessingRunId = "Source Processing Run ID is required for normalization and extraction.";
      } else if (!UUID_REGEX.test(sourceProcessingRunId.trim())) {
        newErrors.sourceProcessingRunId = "Source Processing Run ID must be a valid RFC 4122 UUID.";
      }
    }

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

    const payload: TriggerProcessingRequest = {
      evidence_id: evidenceId.trim(),
      processor_type: processorType as ProcessorType,
      ...(isSourceRunRequired && sourceProcessingRunId.trim()
        ? { source_processing_run_id: sourceProcessingRunId.trim() }
        : {}),
    };

    setValidatedPayload(payload);

    setTimeout(() => {
      setStatus("unconnected");
    }, 400);
  };

  return (
    <div className="space-y-6">
      {status === "unconnected" && validatedPayload && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-[var(--status-info-text)] shrink-0" />
            <p className="font-serif text-xs text-[var(--status-info-text)] font-semibold">
              Processing Trigger Validated Locally — Pipeline Queue Disconnected
            </p>
          </div>
          <p className="font-serif text-xs text-[var(--status-info-text)]">
            Trigger request conforms to contract. Dispatch requires POST <code className="bg-white/60 px-1 py-0.5 rounded">/api/v1/evidence/{evidenceId}/processing</code>.
          </p>
          <div className="bg-white/80 p-2.5 rounded text-xs font-mono border overflow-x-auto text-slate-800">
            {JSON.stringify(validatedPayload, null, 2)}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="Processing trigger form">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="targetEvidenceId" className={errors.evidenceId ? "text-destructive" : ""}>
              Target Evidence ID *
            </Label>
            <Input
              id="targetEvidenceId"
              value={evidenceId}
              onChange={(e) => {
                setEvidenceId(e.target.value);
                if (errors.evidenceId) setErrors((prev) => ({ ...prev, evidenceId: "" }));
              }}
              disabled={status === "submitting"}
              aria-invalid={!!errors.evidenceId}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
              className={errors.evidenceId ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
            />
            {errors.evidenceId && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.evidenceId}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="processorType" className={errors.processorType ? "text-destructive" : ""}>
              Processor Type *
            </Label>
            <Select
              value={processorType}
              onValueChange={(val) => {
                setProcessorType(val as ProcessorType);
                if (errors.processorType) setErrors((prev) => ({ ...prev, processorType: "" }));
              }}
              disabled={status === "submitting"}
            >
              <SelectTrigger id="processorType" className={cn("font-serif text-xs", errors.processorType && "border-destructive focus-visible:ring-destructive/50")}>
                <SelectValue placeholder="Select processor" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="document_ocr">document_ocr (OCR Extract)</SelectItem>
                <SelectItem value="speech_transcription">speech_transcription (ASR)</SelectItem>
                <SelectItem value="language_normalization">language_normalization (Lexicon)</SelectItem>
                <SelectItem value="candidate_extraction">candidate_extraction (Fields)</SelectItem>
              </SelectContent>
            </Select>
            {errors.processorType && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.processorType}
              </p>
            )}
          </div>
        </div>

        {/* Dynamic Source Processing Run ID Field for Normalization / Candidate Extraction */}
        {isSourceRunRequired && (
          <div className="space-y-2 rounded-md bg-slate-50 border p-4">
            <Label htmlFor="sourceProcessingRunId" className={errors.sourceProcessingRunId ? "text-destructive" : ""}>
              Source Processing Run ID (Required for {processorType}) *
            </Label>
            <Input
              id="sourceProcessingRunId"
              value={sourceProcessingRunId}
              onChange={(e) => {
                setSourceProcessingRunId(e.target.value);
                if (errors.sourceProcessingRunId) setErrors((prev) => ({ ...prev, sourceProcessingRunId: "" }));
              }}
              disabled={status === "submitting"}
              aria-invalid={!!errors.sourceProcessingRunId}
              placeholder="UUID of upstream OCR or transcription run"
              className={errors.sourceProcessingRunId ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
            />
            <p className="text-xs text-muted-foreground font-serif">
              Downstream normalization and candidate extraction require the artifact output of a prior successful processing run (BG-006).
            </p>
            {errors.sourceProcessingRunId && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.sourceProcessingRunId}
              </p>
            )}
          </div>
        )}

        {/* Selected Processor Prerequisite Note */}
        {processorType && (
          <div className="rounded bg-muted/40 border p-3 text-xs font-serif text-muted-foreground flex items-start gap-2">
            <Info className="size-3.5 text-secondary mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold text-secondary">
                {PROCESSOR_PREREQUISITES[processorType]?.label}
              </p>
              <p>{PROCESSOR_PREREQUISITES[processorType]?.prereq}</p>
            </div>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <Button type="submit" size="sm" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? (
              "Validating..."
            ) : (
              <>
                <Play className="mr-1.5 size-3.5" />
                Dispatch Processing Run
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
