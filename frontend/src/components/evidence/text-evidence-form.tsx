"use client";

import * as React from "react";
import { AlertCircle, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "cn";

export function TextEvidenceForm() {
  const [caseId, setCaseId] = React.useState("");
  const [consentId, setConsentId] = React.useState("");
  const [textContent, setTextContent] = React.useState("");
  const [sourceLanguage, setSourceLanguage] = React.useState("");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Target Case ID is required.";
    if (!consentId.trim()) newErrors.consentId = "Active Consent ID is required.";
    if (!textContent.trim()) {
      newErrors.textContent = "Text content cannot be empty.";
    } else if (textContent.length > 20000) {
      newErrors.textContent = `Text content exceeds maximum length (20,000 chars). Current: ${textContent.length}`;
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
            Text evidence was validated locally but not registered. Actual registration requires backend integration.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="Text evidence form">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="caseId" className={errors.caseId ? "text-destructive" : ""}>Target Case ID *</Label>
            <Input
              id="caseId"
              value={caseId}
              onChange={(e) => {
                setCaseId(e.target.value);
                if (errors.caseId) setErrors({ ...errors, caseId: "" });
              }}
              disabled={status === "submitting"}
              aria-invalid={!!errors.caseId}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
            />
            {errors.caseId && (
              <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.caseId}
              </p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="consentId" className={errors.consentId ? "text-destructive" : ""}>Consent ID *</Label>
            <Input
              id="consentId"
              value={consentId}
              onChange={(e) => {
                setConsentId(e.target.value);
                if (errors.consentId) setErrors({ ...errors, consentId: "" });
              }}
              disabled={status === "submitting"}
              aria-invalid={!!errors.consentId}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
            />
            {errors.consentId && (
              <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.consentId}
              </p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="sourceLanguage">Source Language (Optional)</Label>
          <Input
            id="sourceLanguage"
            value={sourceLanguage}
            onChange={(e) => setSourceLanguage(e.target.value)}
            disabled={status === "submitting"}
            placeholder="e.g. en"
            className="max-w-[200px]"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <Label htmlFor="textContent" className={errors.textContent ? "text-destructive" : ""}>Text Content *</Label>
            <span className={cn("text-xs font-serif", textContent.length > 20000 ? "text-destructive" : "text-muted-foreground")}>
              {textContent.length} / 20,000
            </span>
          </div>
          <Textarea
            id="textContent"
            value={textContent}
            onChange={(e) => {
              setTextContent(e.target.value);
              if (errors.textContent) setErrors({ ...errors, textContent: "" });
            }}
            disabled={status === "submitting"}
            aria-invalid={!!errors.textContent}
            className={cn("min-h-[200px] resize-y", errors.textContent && "border-destructive focus-visible:ring-destructive/50")}
            placeholder="Enter or paste clinical text here..."
          />
          {errors.textContent && (
            <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
              <AlertCircle className="size-3" /> {errors.textContent}
            </p>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? "Validating..." : (
              <>
                <FileText className="mr-2 size-4" />
                Register Text Evidence
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
