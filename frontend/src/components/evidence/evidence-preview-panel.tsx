"use client";

import * as React from "react";
import { Lock, FileText, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ModalityIcon } from "./modality-icon";
import { EvidenceStateBadge } from "./evidence-state-badge";
import type { EvidenceResponse } from "@/types";

interface EvidencePreviewPanelProps {
  evidence?: EvidenceResponse | null;
}

export function EvidencePreviewPanel({ evidence }: EvidencePreviewPanelProps) {
  if (!evidence) {
    return (
      <div className="border rounded-lg bg-surface p-6 shadow-sm">
        <EmptyState
          icon={<FileText className="size-8 text-muted-foreground" />}
          title="No Evidence Item Selected"
          description="Select an evidence envelope from the ledger above to view its 12 contract metadata properties and processing status."
        />
      </div>
    );
  }

  const isReady = evidence.state === "READY";

  return (
    <div className="border rounded-lg bg-surface p-6 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-muted rounded-md">
            <ModalityIcon modality={evidence.modality} className="size-5" />
          </div>
          <div>
            <h3 className="font-serif font-semibold text-secondary text-base">
              {evidence.original_filename}
            </h3>
            <p className="text-xs font-mono text-muted-foreground truncate max-w-md">
              {evidence.evidence_id}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <EvidenceStateBadge state={evidence.state} />
          <Button variant="outline" size="sm" disabled className="text-xs cursor-not-allowed">
            <Lock className="mr-1.5 size-3" />
            {isReady ? "Download Artifact" : "Download Requires READY State (BG-004)"}
          </Button>
        </div>
      </div>

      {/* 12 Contract Fields Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs font-serif">
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">1. Evidence ID</span>
          <p className="font-mono text-secondary truncate">{evidence.evidence_id}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">2. Case ID</span>
          <p className="font-mono text-secondary truncate">{evidence.case_id}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">3. Encounter ID</span>
          <p className="font-mono text-secondary truncate">{evidence.encounter_id || "Unlinked"}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">4. Modality</span>
          <p className="font-mono text-secondary uppercase font-semibold">{evidence.modality}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">5. State</span>
          <p className="font-mono text-secondary">{evidence.state}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">6. Content Type (MIME)</span>
          <p className="font-mono text-secondary truncate">{evidence.content_type}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">7. Size (Bytes)</span>
          <p className="font-mono text-secondary">
            {evidence.size_bytes.toLocaleString()} bytes ({(evidence.size_bytes / 1024 / 1024).toFixed(2)} MiB)
          </p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">8. Original Filename</span>
          <p className="font-serif text-secondary truncate">{evidence.original_filename}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">9. Source Language</span>
          <p className="font-mono text-secondary">{evidence.source_language || "Unspecified"}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">10. Created By (Actor UUID)</span>
          <p className="font-mono text-secondary truncate">{evidence.created_by}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">11. Created At</span>
          <p className="font-mono text-secondary truncate">{evidence.created_at}</p>
        </div>
        <div className="p-2.5 rounded border bg-slate-50/50 space-y-0.5">
          <span className="text-muted-foreground text-[11px]">12. Provenance</span>
          <p className="font-mono text-secondary truncate">{evidence.provenance}</p>
        </div>
      </div>

      {/* Source Preview Disabled Notice */}
      <div className="rounded-md border border-dashed p-6 text-center bg-slate-50/50 space-y-2">
        <EyeOff className="size-6 text-muted-foreground mx-auto" />
        <h4 className="font-serif font-semibold text-secondary text-sm">
          Binary File Preview Disconnected (BG-004, BG-005)
        </h4>
        <p className="text-xs font-serif text-muted-foreground max-w-md mx-auto">
          In-browser rendering of PDF, audio playback, or image inspection requires authenticated pre-signed object URLs from MinIO/S3, which are gated until scanner promotion to READY state.
        </p>
      </div>
    </div>
  );
}
