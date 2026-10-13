"use client";

import * as React from "react";
import { FileText, AlertCircle, ShieldCheck, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { NarrativeIntakeRequest } from "@/types";

interface NarrativeFormProps {
  caseId: string;
}

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function NarrativeForm({ caseId }: NarrativeFormProps) {
  const [narrativeText, setNarrativeText] = React.useState("");
  const [sourceLanguage, setSourceLanguage] = React.useState("");
  const [encounterId, setEncounterId] = React.useState("");

  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [validatedPayload, setValidatedPayload] = React.useState<NarrativeIntakeRequest | null>(null);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = (): Record<string, string> => {
    const newErrors: Record<string, string> = {};

    const trimmedText = narrativeText.trim();
    if (!trimmedText) {
      newErrors.narrativeText = "Clinical narrative text is required.";
    } else if (trimmedText.length > 20000) {
      newErrors.narrativeText = "Narrative text exceeds maximum length of 20,000 characters.";
    }

    if (encounterId.trim() && !UUID_REGEX.test(encounterId.trim())) {
      newErrors.encounterId = "Encounter ID must be a valid RFC 4122 UUID if specified.";
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

    const payload: NarrativeIntakeRequest = {
      case_id: caseId,
      text: narrativeText.trim(),
      ...(sourceLanguage.trim() ? { source_language: sourceLanguage.trim() } : {}),
      ...(encounterId.trim() ? { encounter_id: encounterId.trim() } : {}),
    };

    setValidatedPayload(payload);

    setTimeout(() => {
      setStatus("unconnected");
    }, 400);
  };

  return (
    <div className="border rounded-lg bg-surface p-6 shadow-sm space-y-6">
      <div className="border-b pb-3">
        <h3 className="font-serif font-semibold text-secondary text-base flex items-center gap-2">
          <FileText className="size-4 text-[var(--ci-teal-700)]" />
          Clinical Narrative Intake (FE-007)
        </h3>
        <p className="text-xs font-serif text-muted-foreground mt-0.5">
          Submit verbatim clinical narrative text or clinician dictation for Case <code className="font-mono text-secondary">{caseId}</code>.
        </p>
      </div>

      <div className="rounded-md bg-amber-50 border border-amber-200 p-3 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold">
          <Info className="size-3.5 text-amber-700 shrink-0" />
          <span>Text Modality Response Contract Caveat (BG-005)</span>
        </div>
        <p>
          Direct text submission registers evidence with modality <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">text</code>. The backend currently returns uppercase <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">TEXT</code> in certain serialization contexts while clients expect lowercase. The frontend normalizes this upon ingest.
        </p>
      </div>

      {status === "unconnected" && validatedPayload && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-[var(--status-info-text)] shrink-0" />
            <p className="font-serif text-xs text-[var(--status-info-text)] font-semibold">
              Narrative Payload Validated Locally (Text Evidence Request)
            </p>
          </div>
          <p className="font-serif text-xs text-[var(--status-info-text)]">
            Text intake validated according to contract limits ({narrativeText.trim().length} characters). Transmission to backend text evidence endpoint is currently disconnected.
          </p>
          <div className="bg-white/80 p-2.5 rounded text-xs font-mono border overflow-x-auto text-slate-800">
            {JSON.stringify(validatedPayload, null, 2)}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" aria-label="Clinical narrative intake form">
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <Label htmlFor="narrativeText" className={errors.narrativeText ? "text-destructive" : ""}>
              Verbatim Clinical Narrative *
            </Label>
            <span className="text-[11px] text-muted-foreground font-mono">
              {narrativeText.length} / 20,000 characters
            </span>
          </div>
          <Textarea
            id="narrativeText"
            value={narrativeText}
            onChange={(e) => {
              setNarrativeText(e.target.value);
              if (errors.narrativeText) setErrors({ ...errors, narrativeText: "" });
            }}
            disabled={status === "submitting"}
            placeholder="Paste or transcribe patient clinical history, symptom timelines, examination findings, or referral text..."
            maxLength={20000}
            rows={8}
            aria-invalid={!!errors.narrativeText}
            className={errors.narrativeText ? "border-destructive font-serif" : "font-serif"}
          />
          {errors.narrativeText && (
            <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1">
              <AlertCircle className="size-3" /> {errors.narrativeText}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="sourceLanguage">
              Source Language (Optional BCP-47 Code)
            </Label>
            <Input
              id="sourceLanguage"
              value={sourceLanguage}
              onChange={(e) => setSourceLanguage(e.target.value)}
              disabled={status === "submitting"}
              placeholder="e.g. en, es, hi-Latn"
              className="font-serif text-xs"
            />
            <p className="text-[11px] text-muted-foreground font-serif">
              Indicates primary natural language for downstream normalization.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="encounterId" className={errors.encounterId ? "text-destructive" : ""}>
              Associated Encounter ID (Optional)
            </Label>
            <Input
              id="encounterId"
              value={encounterId}
              onChange={(e) => {
                setEncounterId(e.target.value);
                if (errors.encounterId) setErrors({ ...errors, encounterId: "" });
              }}
              disabled={status === "submitting"}
              placeholder="Optional Encounter UUID"
              className={errors.encounterId ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
            />
            <p className="text-[11px] text-muted-foreground font-serif">
              Links this narrative to a specific recorded clinical encounter.
            </p>
            {errors.encounterId && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1">
                <AlertCircle className="size-3" /> {errors.encounterId}
              </p>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" size="sm" disabled={status === "submitting"}>
            <FileText className="mr-1.5 size-3.5" />
            {status === "submitting" ? "Validating Narrative..." : "Ingest Narrative"}
          </Button>
        </div>
      </form>
    </div>
  );
}
