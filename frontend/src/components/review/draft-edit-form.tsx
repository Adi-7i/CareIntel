"use client";

import * as React from "react";
import { Edit3, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function DraftEditForm() {
  const [draftId, setDraftId] = React.useState("");
  const [content, setContent] = React.useState("{\n  \n}");
  const [rationale, setRationale] = React.useState("");
  const [expectedDraftVersion, setExpectedDraftVersion] = React.useState("1");
  const [expectedQueueVersion, setExpectedQueueVersion] = React.useState("1");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!draftId.trim()) newErrors.draftId = "Draft ID is required.";
    
    try {
      JSON.parse(content);
    } catch {
      newErrors.content = "Must be valid JSON.";
    }

    const vD = parseInt(expectedDraftVersion, 10);
    const vQ = parseInt(expectedQueueVersion, 10);
    if (isNaN(vD) || vD < 1) newErrors.expectedDraftVersion = "Must be >= 1.";
    if (isNaN(vQ) || vQ < 1) newErrors.expectedQueueVersion = "Must be >= 1.";
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
    setTimeout(() => setStatus("unconnected"), 800);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="rounded-md bg-muted border p-4 mb-4 max-w-xl">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          Local Editing Notice
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          Edited content must be valid JSON matching the unverified schema. This content is <strong>NOT persisted</strong> in this unconnected phase.
        </p>
      </div>

      <div className="space-y-2 max-w-md">
        <Label htmlFor="deDraftId" className={errors.draftId ? "text-destructive" : ""}>Draft ID *</Label>
        <Input id="deDraftId" value={draftId} onChange={(e) => { setDraftId(e.target.value); if (errors.draftId) setErrors({ ...errors, draftId: "" }); }} disabled={status === "submitting"} />
        {errors.draftId && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.draftId}</p>}
      </div>

      <div className="space-y-2 max-w-xl">
        <Label htmlFor="deContent" className={errors.content ? "text-destructive" : ""}>Edited Content (JSON) *</Label>
        <Textarea id="deContent" value={content} onChange={(e) => { setContent(e.target.value); if (errors.content) setErrors({ ...errors, content: "" }); }} disabled={status === "submitting"} rows={6} className="font-mono text-sm" />
        {errors.content && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.content}</p>}
      </div>

      <div className="space-y-2 max-w-xl">
        <Label htmlFor="deRationale">Rationale (Optional)</Label>
        <Textarea id="deRationale" value={rationale} onChange={(e) => setRationale(e.target.value)} disabled={status === "submitting"} rows={3} maxLength={4000} />
      </div>

      <div className="grid sm:grid-cols-2 gap-4 max-w-md">
        <div className="space-y-2">
          <Label htmlFor="deDraftVer" className={errors.expectedDraftVersion ? "text-destructive" : ""}>Expected Draft Ver. *</Label>
          <Input id="deDraftVer" type="number" min="1" value={expectedDraftVersion} onChange={(e) => { setExpectedDraftVersion(e.target.value); if (errors.expectedDraftVersion) setErrors({ ...errors, expectedDraftVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedDraftVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedDraftVersion}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="deQueueVer" className={errors.expectedQueueVersion ? "text-destructive" : ""}>Expected Queue Ver. *</Label>
          <Input id="deQueueVer" type="number" min="1" value={expectedQueueVersion} onChange={(e) => { setExpectedQueueVersion(e.target.value); if (errors.expectedQueueVersion) setErrors({ ...errors, expectedQueueVersion: "" }); }} disabled={status === "submitting"} />
          {errors.expectedQueueVersion && <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1"><AlertCircle className="size-3" /> {errors.expectedQueueVersion}</p>}
        </div>
      </div>

      {status === "unconnected" && (
        <p className="font-serif text-sm text-[var(--status-info-text)] bg-[var(--status-info-surface)] p-2 rounded max-w-md">
          Validated locally. Requires backend integration.
        </p>
      )}
      <Button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Submitting..." : <><Edit3 className="mr-2 size-4" />Submit Edits</>}
      </Button>
    </form>
  );
}
