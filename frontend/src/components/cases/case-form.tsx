"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Save, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function CaseForm() {
  const [title, setTitle] = React.useState("");
  const [patientId, setPatientId] = React.useState("");
  const [priority, setPriority] = React.useState("");
  const [hasConsent, setHasConsent] = React.useState(false);
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!title.trim()) newErrors.title = "Case title is required.";
    if (!patientId.trim()) newErrors.patientId = "Patient identifier is required.";
    if (!priority) newErrors.priority = "Priority must be selected.";
    if (!hasConsent) newErrors.consent = "Active data processing consent is required to create a case.";
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
    <div className="space-y-8 max-w-3xl">
      <div className="flex items-center gap-4">
        <Button render={<Link href="/cases" />} variant="outline" size="icon" aria-label="Back to cases">
          <ArrowLeft className="size-4" />
        </Button>
        <div>
          <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">Create Case</h1>
          <p className="font-serif text-sm text-muted-foreground mt-1">Initialize a new clinical review workflow.</p>
        </div>
      </div>

      {status === "unconnected" && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4">
          <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold mb-1">
            Authentication & Persistence Disconnected
          </p>
          <p className="font-serif text-sm text-[var(--status-info-text)]">
            Case validated locally but not saved. Actual creation requires backend integration.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8" aria-label="Case creation form">
        {/* Section: Overview */}
        <div className="space-y-6 bg-surface p-6 rounded-lg border shadow-sm">
          <h2 className="font-serif text-lg font-semibold border-b pb-2 text-secondary">Case Overview</h2>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title" className={errors.title ? "text-destructive" : ""}>Case Title *</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  if (errors.title) setErrors({ ...errors, title: "" });
                }}
                disabled={status === "submitting"}
                aria-invalid={!!errors.title}
                className={errors.title ? "border-destructive focus-visible:ring-destructive/50" : ""}
                placeholder="e.g. Cardiology Consult Review"
              />
              {errors.title && (
                <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" /> {errors.title}
                </p>
              )}
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="patientId" className={errors.patientId ? "text-destructive" : ""}>Patient Identifier *</Label>
                <Input
                  id="patientId"
                  value={patientId}
                  onChange={(e) => {
                    setPatientId(e.target.value);
                    if (errors.patientId) setErrors({ ...errors, patientId: "" });
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.patientId}
                  className={errors.patientId ? "border-destructive focus-visible:ring-destructive/50" : ""}
                  placeholder="MRN or distinct ID"
                />
                {errors.patientId && (
                  <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.patientId}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="priority" className={errors.priority ? "text-destructive" : ""}>Priority *</Label>
                <Select
                  value={priority}
                  onValueChange={(val) => {
                    setPriority(val || "");
                    if (errors.priority) setErrors({ ...errors, priority: "" });
                  }}
                  disabled={status === "submitting"}
                >
                  <SelectTrigger id="priority" className={errors.priority ? "border-destructive focus-visible:ring-destructive/50" : ""}>
                    <SelectValue placeholder="Select priority" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="routine">Routine</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="stat">STAT (Immediate)</SelectItem>
                  </SelectContent>
                </Select>
                {errors.priority && (
                  <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.priority}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Section: Consent */}
        <div className="space-y-6 bg-surface p-6 rounded-lg border shadow-sm">
          <h2 className="font-serif text-lg font-semibold border-b pb-2 text-secondary">Data Processing Consent</h2>
          <div className="flex items-start space-x-3">
            <div className="flex h-5 items-center">
              <input
                id="consent"
                type="checkbox"
                checked={hasConsent}
                onChange={(e) => {
                  setHasConsent(e.target.checked);
                  if (errors.consent) setErrors({ ...errors, consent: "" });
                }}
                disabled={status === "submitting"}
                className="size-4 rounded border-input bg-transparent shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
            <div className="space-y-1 leading-none">
              <Label htmlFor="consent" className={`font-serif text-base ${errors.consent ? "text-destructive" : ""}`}>
                I verify that active data processing consent has been obtained for this subject.
              </Label>
              <p className="text-sm text-muted-foreground font-serif pt-1">
                Required by CareIntel policy before case initialization.
              </p>
              {errors.consent && (
                <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-2">
                  <AlertCircle className="size-3" /> {errors.consent}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button type="button" variant="ghost" render={<Link href="/cases" />} disabled={status === "submitting"}>
            Cancel
          </Button>
          <Button type="submit" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? "Validating..." : (
              <>
                <Save className="mr-2 size-4" />
                Create Case
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
