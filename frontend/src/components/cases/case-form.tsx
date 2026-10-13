"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Save, AlertCircle, Info, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { CreateCaseRequest } from "@/types";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function CaseForm() {
  const [syntheticSubjectId, setSyntheticSubjectId] = React.useState("");
  const [consentId, setConsentId] = React.useState("");
  const [facilityId, setFacilityId] = React.useState("");

  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [validatedPayload, setValidatedPayload] = React.useState<CreateCaseRequest | null>(null);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = (): Record<string, string> => {
    const newErrors: Record<string, string> = {};

    if (!syntheticSubjectId.trim()) {
      newErrors.syntheticSubjectId = "Synthetic Subject ID is required.";
    } else if (!UUID_REGEX.test(syntheticSubjectId.trim())) {
      newErrors.syntheticSubjectId = "Synthetic Subject ID must be a valid RFC 4122 UUID.";
    }

    if (!consentId.trim()) {
      newErrors.consentId = "Active Consent ID is required.";
    } else if (!UUID_REGEX.test(consentId.trim())) {
      newErrors.consentId = "Consent ID must be a valid RFC 4122 UUID.";
    }

    if (facilityId.trim() && !UUID_REGEX.test(facilityId.trim())) {
      newErrors.facilityId = "Facility ID must be a valid RFC 4122 UUID if provided.";
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

    const payload: CreateCaseRequest = {
      synthetic_subject_id: syntheticSubjectId.trim(),
      consent_id: consentId.trim(),
      ...(facilityId.trim() ? { facility_id: facilityId.trim() } : {}),
    };

    setValidatedPayload(payload);

    setTimeout(() => {
      setStatus("unconnected");
    }, 400);
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <div className="flex items-center gap-4">
        <Button render={<Link href="/cases" />} variant="outline" size="icon" aria-label="Back to cases">
          <ArrowLeft className="size-4" />
        </Button>
        <div>
          <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">Create Case</h1>
          <p className="font-serif text-sm text-muted-foreground mt-1">
            Initialize a new case record according to CreateCaseRequest contract.
          </p>
        </div>
      </div>

      {/* Advisory & Architectural Boundary Notice */}
      <div className="rounded-md bg-slate-50 border border-slate-200 p-4 space-y-2">
        <div className="flex items-start gap-2">
          <Info className="size-4 text-[var(--ci-teal-700)] mt-0.5 shrink-0" />
          <div className="text-xs font-serif text-slate-700 leading-relaxed space-y-1">
            <p className="font-semibold text-secondary">
              Identity & Urgency Architecture (DEC-01, requirement.md §6)
            </p>
            <p>
              Cases are initialized strictly via <code className="bg-slate-200 px-1 py-0.5 rounded">CreateCaseRequest</code> with synthetic subject and consent UUIDs. CareIntel case records do not store patient names, MRNs, age, sex, or clinical departments.
            </p>
            <p className="text-muted-foreground">
              Clinical Urgency: <span className="font-semibold text-secondary">Unassigned</span> (clinical priority is derived solely through qualified reviewer evaluation, not client form inputs).
            </p>
          </div>
        </div>
      </div>

      {status === "unconnected" && validatedPayload && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-5 text-[var(--status-info-text)] shrink-0" />
            <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold">
              Form Validated Locally — Backend Disconnected (BG-001, BG-011)
            </p>
          </div>
          <p className="font-serif text-xs text-[var(--status-info-text)] leading-relaxed">
            Case payload conforms to the contract. Actual case initialization requires POST <code className="bg-white/60 px-1 py-0.5 rounded">/api/v1/cases</code> with active consent verification and identity provisioning.
          </p>
          <div className="bg-white/80 p-3 rounded text-xs font-mono border overflow-x-auto text-slate-800">
            {JSON.stringify(validatedPayload, null, 2)}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8" aria-label="Case creation form">
        {/* Section: Identifiers */}
        <div className="space-y-6 bg-surface p-6 rounded-lg border shadow-sm">
          <h2 className="font-serif text-lg font-semibold border-b pb-2 text-secondary">Contract Identifiers</h2>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="syntheticSubjectId" className={errors.syntheticSubjectId ? "text-destructive" : ""}>
                Synthetic Subject ID *
              </Label>
              <Input
                id="syntheticSubjectId"
                value={syntheticSubjectId}
                onChange={(e) => {
                  setSyntheticSubjectId(e.target.value);
                  if (errors.syntheticSubjectId) setErrors({ ...errors, syntheticSubjectId: "" });
                }}
                disabled={status === "submitting"}
                aria-invalid={!!errors.syntheticSubjectId}
                className={errors.syntheticSubjectId ? "border-destructive focus-visible:ring-destructive/50" : ""}
                placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
              />
              <p className="text-xs text-muted-foreground font-serif">
                Must be an existing synthetic subject UUID. Subject lookup API currently unavailable (BG-001).
              </p>
              {errors.syntheticSubjectId && (
                <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" /> {errors.syntheticSubjectId}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="consentId" className={errors.consentId ? "text-destructive" : ""}>
                Active Consent ID *
              </Label>
              <Input
                id="consentId"
                value={consentId}
                onChange={(e) => {
                  setConsentId(e.target.value);
                  if (errors.consentId) setErrors({ ...errors, consentId: "" });
                }}
                disabled={status === "submitting"}
                aria-invalid={!!errors.consentId}
                className={errors.consentId ? "border-destructive focus-visible:ring-destructive/50" : ""}
                placeholder="e.g. 6ba7b810-9dad-11d1-80b4-00c04fd430c8"
              />
              <p className="text-xs text-muted-foreground font-serif">
                Must be an active consent record for data processing purpose with notice version 1.0 (BG-003).
              </p>
              {errors.consentId && (
                <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" /> {errors.consentId}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="facilityId" className={errors.facilityId ? "text-destructive" : ""}>
                Facility ID (Optional)
              </Label>
              <Input
                id="facilityId"
                value={facilityId}
                onChange={(e) => {
                  setFacilityId(e.target.value);
                  if (errors.facilityId) setErrors({ ...errors, facilityId: "" });
                }}
                disabled={status === "submitting"}
                aria-invalid={!!errors.facilityId}
                className={errors.facilityId ? "border-destructive focus-visible:ring-destructive/50" : ""}
                placeholder="Optional facility UUID"
              />
              <p className="text-xs text-muted-foreground font-serif">
                Optional originating healthcare facility UUID. Facility discovery currently unavailable (BG-015).
              </p>
              {errors.facilityId && (
                <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" /> {errors.facilityId}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Informational Summary */}
        <div className="rounded-md bg-muted/40 border p-4 text-xs font-serif text-muted-foreground space-y-1">
          <p className="font-semibold text-secondary">Initial Case State Lifecycle</p>
          <p>
            Upon successful creation, the case state begins at <code className="bg-slate-200 px-1 py-0.5 rounded text-secondary font-mono">CREATED</code> with version <code className="bg-slate-200 px-1 py-0.5 rounded text-secondary font-mono">1</code>. State transitions occur strictly through validated lifecycle events.
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button type="button" variant="ghost" render={<Link href="/cases" />} disabled={status === "submitting"}>
            Cancel
          </Button>
          <Button type="submit" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? (
              "Validating..."
            ) : (
              <>
                <Save className="mr-2 size-4" />
                Initialize Case
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
