"use client";

import * as React from "react";
import { AlertCircle, FileText, Info, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "cn";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

interface TextEvidenceFormProps {
  caseId?: string;
  consentId?: string;
}

export function TextEvidenceForm({ caseId: initialCaseId = "", consentId: initialConsentId = "" }: TextEvidenceFormProps) {
  const [caseId, setCaseId] = React.useState(initialCaseId);
  const [consentId, setConsentId] = React.useState(initialConsentId);
  const [textContent, setTextContent] = React.useState("");
  const [sourceLanguage, setSourceLanguage] = React.useState("");

  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [validatedData, setValidatedData] = React.useState<{
    case_id: string;
    consent_id: string;
    modality: string;
    text_length: number;
    source_language?: string;
  } | null>(null);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) {
      newErrors.caseId = "Target Case ID is required.";
    } else if (!UUID_REGEX.test(caseId.trim())) {
      newErrors.caseId = "Case ID must be a valid RFC 4122 UUID.";
    }

    if (!consentId.trim()) {
      newErrors.consentId = "Active Consent ID is required.";
    } else if (!UUID_REGEX.test(consentId.trim())) {
      newErrors.consentId = "Consent ID must be a valid RFC 4122 UUID.";
    }

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

    setValidatedData({
      case_id: caseId.trim(),
      consent_id: consentId.trim(),
      modality: "text",
      text_length: textContent.trim().length,
      ...(sourceLanguage.trim() ? { source_language: sourceLanguage.trim() } : {}),
    });

    setTimeout(() => {
      setStatus("unconnected");
    }, 400);
  };

  return (
    <div className="space-y-6">
      <div className="rounded-md bg-amber-50 border border-amber-200 p-3 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold">
          <Info className="size-3.5 text-amber-700 shrink-0" />
          <span>Text Modality Response Caveat (BG-005)</span>
        </div>
        <p>
          Backend contracts register text intake with modality <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">text</code>. Certain backend serialization responses emit uppercase <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">TEXT</code>; the frontend normalizes both safely.
        </p>
      </div>

      {status === "unconnected" && validatedData && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-[var(--status-info-text)] shrink-0" />
            <p className="font-serif text-xs text-[var(--status-info-text)] font-semibold">
              Text Evidence Validated Locally — Registration Disconnected
            </p>
          </div>
          <p className="font-serif text-xs text-[var(--status-info-text)]">
            Payload validated ({validatedData.text_length} characters). Registration requires POST <code className="bg-white/60 px-1 py-0.5 rounded">/api/v1/cases/{caseId}/evidence/text</code>.
          </p>
          <div className="bg-white/80 p-2.5 rounded text-xs font-mono border overflow-x-auto text-slate-800">
            {JSON.stringify(validatedData, null, 2)}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="Text evidence form">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="caseId" className={errors.caseId ? "text-destructive" : ""}>
              Target Case ID *
            </Label>
            <Input
              id="caseId"
              value={caseId}
              onChange={(e) => {
                setCaseId(e.target.value);
                if (errors.caseId) setErrors((prev) => ({ ...prev, caseId: "" }));
              }}
              disabled={status === "submitting" || Boolean(initialCaseId)}
              aria-invalid={!!errors.caseId}
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
              className={errors.caseId ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
            />
            {errors.caseId && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.caseId}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="consentId" className={errors.consentId ? "text-destructive" : ""}>
              Consent ID *
            </Label>
            <Input
              id="consentId"
              value={consentId}
              onChange={(e) => {
                setConsentId(e.target.value);
                if (errors.consentId) setErrors((prev) => ({ ...prev, consentId: "" }));
              }}
              disabled={status === "submitting"}
              aria-invalid={!!errors.consentId}
              placeholder="Active consent UUID (BG-003)"
              className={errors.consentId ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
            />
            {errors.consentId && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.consentId}
              </p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="sourceLanguage">Source Language (Optional BCP-47)</Label>
          <Input
            id="sourceLanguage"
            value={sourceLanguage}
            onChange={(e) => setSourceLanguage(e.target.value)}
            disabled={status === "submitting"}
            placeholder="e.g. en"
            className="max-w-[200px] font-serif text-xs"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <Label htmlFor="textContent" className={errors.textContent ? "text-destructive" : ""}>
              Clinical Text Content *
            </Label>
            <span className={cn("text-xs font-serif font-mono", textContent.length > 20000 ? "text-destructive" : "text-muted-foreground")}>
              {textContent.length} / 20,000 chars
            </span>
          </div>
          <Textarea
            id="textContent"
            value={textContent}
            onChange={(e) => {
              setTextContent(e.target.value);
              if (errors.textContent) setErrors((prev) => ({ ...prev, textContent: "" }));
            }}
            disabled={status === "submitting"}
            aria-invalid={!!errors.textContent}
            className={cn("min-h-[160px] resize-y font-serif", errors.textContent && "border-destructive focus-visible:ring-destructive/50")}
            placeholder="Enter clinical notes, laboratory reports, or diagnostic transcripts..."
            maxLength={20000}
          />
          {errors.textContent && (
            <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
              <AlertCircle className="size-3" /> {errors.textContent}
            </p>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" size="sm" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? (
              "Validating..."
            ) : (
              <>
                <FileText className="mr-1.5 size-3.5" />
                Register Text Evidence
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
