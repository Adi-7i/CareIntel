"use client";

import * as React from "react";
import { PlusCircle, AlertCircle, ShieldCheck, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { CreateEncounterRequest } from "@/types";

interface EncounterFormProps {
  caseId: string;
}

export function EncounterForm({ caseId }: EncounterFormProps) {
  const [encounterType, setEncounterType] = React.useState("");
  const [occurredAt, setOccurredAt] = React.useState("");
  const [notes, setNotes] = React.useState("");

  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [validatedPayload, setValidatedPayload] = React.useState<CreateEncounterRequest | null>(null);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = (): Record<string, string> => {
    const newErrors: Record<string, string> = {};

    const trimmedType = encounterType.trim();
    if (!trimmedType) {
      newErrors.encounterType = "Encounter type is required.";
    } else if (trimmedType.length > 100) {
      newErrors.encounterType = "Encounter type must not exceed 100 characters.";
    }

    if (!occurredAt.trim()) {
      newErrors.occurredAt = "Encounter timestamp (occurred_at) is required.";
    } else {
      const parsedDate = new Date(occurredAt);
      if (isNaN(parsedDate.getTime())) {
        newErrors.occurredAt = "Please enter a valid datetime string.";
      }
    }

    if (notes.length > 2000) {
      newErrors.notes = "Notes must not exceed 2000 characters.";
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

    const payload: CreateEncounterRequest = {
      case_id: caseId,
      encounter_type: encounterType.trim(),
      occurred_at: new Date(occurredAt).toISOString(),
      ...(notes.trim() ? { notes: notes.trim() } : {}),
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
          <Clock className="size-4 text-[var(--ci-teal-700)]" />
          Log Clinical Encounter
        </h3>
        <p className="text-xs font-serif text-muted-foreground mt-0.5">
          Record an in-person, telemedicine, or emergency encounter associated with Case <code className="font-mono text-secondary">{caseId}</code>.
        </p>
      </div>

      {status === "unconnected" && validatedPayload && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-[var(--status-info-text)] shrink-0" />
            <p className="font-serif text-xs text-[var(--status-info-text)] font-semibold">
              Encounter Payload Validated Locally (CreateEncounterRequest)
            </p>
          </div>
          <p className="font-serif text-xs text-[var(--status-info-text)]">
            Encounter validated according to contract rules. Encounter creation API integration pending (POST /api/v1/cases/{caseId}/encounters).
          </p>
          <div className="bg-white/80 p-2.5 rounded text-xs font-mono border overflow-x-auto text-slate-800">
            {JSON.stringify(validatedPayload, null, 2)}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" aria-label="Clinical encounter form">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="encounterType" className={errors.encounterType ? "text-destructive" : ""}>
              Encounter Type *
            </Label>
            <Input
              id="encounterType"
              value={encounterType}
              onChange={(e) => {
                setEncounterType(e.target.value);
                if (errors.encounterType) setErrors({ ...errors, encounterType: "" });
              }}
              disabled={status === "submitting"}
              placeholder="e.g. Inpatient Admission, Triage Assessment"
              maxLength={100}
              aria-invalid={!!errors.encounterType}
              className={errors.encounterType ? "border-destructive" : ""}
            />
            <div className="flex justify-between text-[11px] text-muted-foreground font-serif">
              <span>Required (1–100 characters)</span>
              <span>{encounterType.length}/100</span>
            </div>
            {errors.encounterType && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1">
                <AlertCircle className="size-3" /> {errors.encounterType}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="occurredAt" className={errors.occurredAt ? "text-destructive" : ""}>
              Occurred At Timestamp *
            </Label>
            <Input
              id="occurredAt"
              type="datetime-local"
              value={occurredAt}
              onChange={(e) => {
                setOccurredAt(e.target.value);
                if (errors.occurredAt) setErrors({ ...errors, occurredAt: "" });
              }}
              disabled={status === "submitting"}
              aria-invalid={!!errors.occurredAt}
              className={errors.occurredAt ? "border-destructive" : ""}
            />
            <p className="text-[11px] text-muted-foreground font-serif">
              Stored as UTC ISO-8601 with timezone normalization.
            </p>
            {errors.occurredAt && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1">
                <AlertCircle className="size-3" /> {errors.occurredAt}
              </p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <Label htmlFor="notes" className={errors.notes ? "text-destructive" : ""}>
              Clinical Context Notes (Optional)
            </Label>
            <span className="text-[11px] text-muted-foreground font-mono">
              {notes.length} / 2000 chars
            </span>
          </div>
          <Textarea
            id="notes"
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              if (errors.notes) setErrors({ ...errors, notes: "" });
            }}
            disabled={status === "submitting"}
            placeholder="Administrative or location context for this encounter..."
            maxLength={2000}
            rows={3}
            aria-invalid={!!errors.notes}
            className={errors.notes ? "border-destructive" : ""}
          />
          {errors.notes && (
            <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1">
              <AlertCircle className="size-3" /> {errors.notes}
            </p>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" size="sm" disabled={status === "submitting"}>
            <PlusCircle className="mr-1.5 size-3.5" />
            {status === "submitting" ? "Validating..." : "Save Encounter"}
          </Button>
        </div>
      </form>
    </div>
  );
}
