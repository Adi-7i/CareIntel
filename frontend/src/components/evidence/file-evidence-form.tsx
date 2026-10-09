"use client";

import * as React from "react";
import { Upload, AlertCircle, FileUp, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EvidenceModality, ModalityIcon } from "./modality-icon";
import { cn } from "cn";

const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".mp3", ".wav", ".m4a", ".ogg"];

export function FileEvidenceForm() {
  const [caseId, setCaseId] = React.useState("");
  const [consentId, setConsentId] = React.useState("");
  const [modality, setModality] = React.useState<EvidenceModality | "">("");
  const [file, setFile] = React.useState<File | null>(null);
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      if (!selectedFile) return;
      
      const ext = "." + selectedFile.name.split('.').pop()?.toLowerCase();
      
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setErrors({ ...errors, file: `Extension ${ext} is not supported. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}` });
        setFile(null);
      } else {
        setFile(selectedFile);
        if (errors.file) setErrors({ ...errors, file: "" });
      }
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Target Case ID is required.";
    if (!consentId.trim()) newErrors.consentId = "Active Consent ID is required.";
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
            File selection and metadata were validated locally. Actual multipart upload requires backend integration.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="File evidence form">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="fileCaseId" className={errors.caseId ? "text-destructive" : ""}>Target Case ID *</Label>
            <Input
              id="fileCaseId"
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
            <Label htmlFor="fileConsentId" className={errors.consentId ? "text-destructive" : ""}>Consent ID *</Label>
            <Input
              id="fileConsentId"
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
          <Label htmlFor="modality" className={errors.modality ? "text-destructive" : ""}>Modality *</Label>
          <Select
            value={modality}
            onValueChange={(val) => {
              setModality(val as EvidenceModality);
              if (errors.modality) setErrors({ ...errors, modality: "" });
            }}
            disabled={status === "submitting"}
          >
            <SelectTrigger id="modality" className={cn("max-w-[200px]", errors.modality && "border-destructive focus-visible:ring-destructive/50")}>
              <SelectValue placeholder="Select modality" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="text">Text</SelectItem>
              <SelectItem value="document">Document</SelectItem>
              <SelectItem value="image">Image</SelectItem>
              <SelectItem value="audio">Audio</SelectItem>
            </SelectContent>
          </Select>
          {errors.modality && (
            <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
              <AlertCircle className="size-3" /> {errors.modality}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label className={errors.file ? "text-destructive" : ""}>File Selection *</Label>
          
          {!file ? (
            <div className={cn("border-2 border-dashed rounded-lg p-8 text-center bg-muted/20 hover:bg-muted/40 transition-colors", errors.file && "border-destructive/50 bg-destructive/5")}>
              <Input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={handleFileChange}
                disabled={status === "submitting"}
                accept={ALLOWED_EXTENSIONS.join(",")}
              />
              <Label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-3">
                <div className="p-3 bg-background border rounded-full shadow-sm">
                  <Upload className="size-5 text-secondary" />
                </div>
                <div>
                  <p className="font-serif font-medium text-secondary">Click to browse files</p>
                  <p className="text-sm text-muted-foreground mt-1 max-w-xs mx-auto">
                    Supported: PDF, DOCX, TXT, JPG, PNG, MP3, WAV, M4A, OGG
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Size limits are enforced by the server on upload.
                  </p>
                </div>
              </Label>
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 border rounded-lg bg-surface shadow-sm">
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="p-2 bg-muted rounded-md shrink-0">
                  <ModalityIcon modality={(modality as EvidenceModality) || "document"} className="size-6" />
                </div>
                <div className="truncate">
                  <p className="font-serif font-medium text-sm text-secondary truncate">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
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
            <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
              <AlertCircle className="size-3" /> {errors.file}
            </p>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={status === "submitting"} aria-busy={status === "submitting"}>
            {status === "submitting" ? "Validating..." : (
              <>
                <FileUp className="mr-2 size-4" />
                Upload File Evidence
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
