"use client";

import * as React from "react";
import { Upload, AlertCircle, FileUp, X, Info, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ModalityIcon } from "./modality-icon";
import type { EvidenceModality } from "@/types";
import { cn } from "cn";

const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".mp3", ".wav", ".m4a", ".ogg"];
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MiB configurable server limit
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

interface FileEvidenceFormProps {
  caseId?: string;
  consentId?: string;
}

export function FileEvidenceForm({ caseId: initialCaseId = "", consentId: initialConsentId = "" }: FileEvidenceFormProps) {
  const [caseId, setCaseId] = React.useState(initialCaseId);
  const [consentId, setConsentId] = React.useState(initialConsentId);
  const [modality, setModality] = React.useState<EvidenceModality | "">("");
  const [sourceLanguage, setSourceLanguage] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);

  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [validatedData, setValidatedData] = React.useState<{
    case_id: string;
    consent_id: string;
    modality: string;
    filename: string;
    size_bytes: number;
    content_type: string;
    source_language?: string;
  } | null>(null);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      if (!selectedFile) return;

      const ext = "." + (selectedFile.name.split(".").pop()?.toLowerCase() || "");

      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setErrors((prev) => ({
          ...prev,
          file: `Extension ${ext} is not supported. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`,
        }));
        setFile(null);
        return;
      }

      if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
        setErrors((prev) => ({
          ...prev,
          file: `File size exceeds the 50 MiB maximum limit (${(selectedFile.size / 1024 / 1024).toFixed(1)} MiB).`,
        }));
        setFile(null);
        return;
      }

      setFile(selectedFile);
      setErrors((prev) => ({ ...prev, file: "" }));

      // Auto-suggest modality from extension if not chosen
      if (!modality) {
        if ([".pdf", ".docx"].includes(ext)) setModality("document");
        else if ([".jpg", ".jpeg", ".png"].includes(ext)) setModality("image");
        else if ([".mp3", ".wav", ".m4a", ".ogg"].includes(ext)) setModality("audio");
        else if ([".txt"].includes(ext)) setModality("text");
      }
    }
  };

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

    if (!modality) newErrors.modality = "Evidence modality must be selected.";
    if (!file) newErrors.file = "A valid file must be selected.";

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

    if (file) {
      setValidatedData({
        case_id: caseId.trim(),
        consent_id: consentId.trim(),
        modality,
        filename: file.name,
        size_bytes: file.size,
        content_type: file.type || "application/octet-stream",
        ...(sourceLanguage.trim() ? { source_language: sourceLanguage.trim() } : {}),
      });
    }

    setTimeout(() => {
      setStatus("unconnected");
    }, 400);
  };

  return (
    <div className="space-y-6">
      {/* Scanner & Pipeline Notice */}
      <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-semibold">
          <Info className="size-4 text-amber-700 shrink-0" />
          <span>Upload Scanning Pipeline Status (BG-004)</span>
        </div>
        <p>
          Uploaded files register in <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">STORED</code> state. The active backend scanner is <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">NoOpScanner</code> — files cannot advance to <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">READY</code> without an external antivirus/content scanner configured. Processing and download require <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">READY</code> state.
        </p>
      </div>

      {status === "unconnected" && validatedData && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-[var(--status-info-text)] shrink-0" />
            <p className="font-serif text-xs text-[var(--status-info-text)] font-semibold">
              Multipart Payload Validated Locally — Upload Endpoint Disconnected
            </p>
          </div>
          <p className="font-serif text-xs text-[var(--status-info-text)]">
            Evidence envelope validated ({validatedData.filename}, {(validatedData.size_bytes / 1024 / 1024).toFixed(2)} MiB). In frontend-only mode, files are not transmitted to object storage.
          </p>
          <div className="bg-white/80 p-2.5 rounded text-xs font-mono border overflow-x-auto text-slate-800">
            {JSON.stringify(validatedData, null, 2)}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="File evidence form">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="fileCaseId" className={errors.caseId ? "text-destructive" : ""}>
              Target Case ID *
            </Label>
            <Input
              id="fileCaseId"
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
            <Label htmlFor="fileConsentId" className={errors.consentId ? "text-destructive" : ""}>
              Consent ID *
            </Label>
            <Input
              id="fileConsentId"
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

        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="modality" className={errors.modality ? "text-destructive" : ""}>
              Evidence Modality *
            </Label>
            <Select
              value={modality}
              onValueChange={(val) => {
                setModality(val as EvidenceModality);
                if (errors.modality) setErrors((prev) => ({ ...prev, modality: "" }));
              }}
              disabled={status === "submitting"}
            >
              <SelectTrigger id="modality" className={cn("w-full font-serif text-xs", errors.modality && "border-destructive focus-visible:ring-destructive/50")}>
                <SelectValue placeholder="Select modality" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="document">document (PDF, DOCX)</SelectItem>
                <SelectItem value="image">image (JPG, PNG)</SelectItem>
                <SelectItem value="audio">audio (MP3, WAV, M4A, OGG)</SelectItem>
                <SelectItem value="text">text (Plain Text Document)</SelectItem>
              </SelectContent>
            </Select>
            {errors.modality && (
              <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                <AlertCircle className="size-3" /> {errors.modality}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="fileSourceLanguage">
              Source Language (Optional BCP-47)
            </Label>
            <Input
              id="fileSourceLanguage"
              value={sourceLanguage}
              onChange={(e) => setSourceLanguage(e.target.value)}
              disabled={status === "submitting"}
              placeholder="e.g. en, es, hi-Latn"
              className="font-serif text-xs"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label className={errors.file ? "text-destructive" : ""}>File Selection *</Label>

          {!file ? (
            <div
              className={cn(
                "border-2 border-dashed rounded-lg p-6 text-center bg-muted/20 hover:bg-muted/40 transition-colors",
                errors.file && "border-destructive/50 bg-destructive/5"
              )}
            >
              <Input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={handleFileChange}
                disabled={status === "submitting"}
                accept={ALLOWED_EXTENSIONS.join(",")}
              />
              <Label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-2">
                <div className="p-2.5 bg-background border rounded-full shadow-sm">
                  <Upload className="size-5 text-secondary" />
                </div>
                <div>
                  <p className="font-serif font-medium text-secondary text-sm">Click to browse file</p>
                  <p className="text-xs text-muted-foreground mt-0.5 max-w-sm mx-auto font-serif">
                    Allowed: PDF, DOCX, TXT, JPG, PNG, MP3, WAV, M4A, OGG (Max 50 MiB server limit)
                  </p>
                </div>
              </Label>
            </div>
          ) : (
            <div className="flex items-center justify-between p-3.5 border rounded-lg bg-surface shadow-sm">
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="p-2 bg-muted rounded-md shrink-0">
                  <ModalityIcon modality={(modality as EvidenceModality) || "document"} className="size-5" />
                </div>
                <div className="truncate">
                  <p className="font-serif font-medium text-xs text-secondary truncate">{file.name}</p>
                  <p className="text-[11px] text-muted-foreground font-mono">
                    {(file.size / 1024 / 1024).toFixed(2)} MiB • {file.type || "unknown mime"}
                  </p>
                </div>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setFile(null)}
                disabled={status === "submitting"}
                aria-label="Remove file"
              >
                <X className="size-4" />
              </Button>
            </div>
          )}

          {errors.file && (
            <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
              <AlertCircle className="size-3" /> {errors.file}
            </p>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" size="sm" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? (
              "Validating..."
            ) : (
              <>
                <FileUp className="mr-1.5 size-3.5" />
                Upload Evidence File
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
