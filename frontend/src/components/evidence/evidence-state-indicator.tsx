"use client";

import * as React from "react";
import { ShieldCheck, Lock } from "lucide-react";
import type { EvidenceState } from "@/types";

interface EvidenceStateIndicatorProps {
  currentState?: EvidenceState;
}

export function EvidenceStateIndicator({ currentState = "STORED" }: EvidenceStateIndicatorProps) {
  const steps: { state: EvidenceState; label: string; desc: string }[] = [
    { state: "PENDING_UPLOAD", label: "Pending Upload", desc: "Multipart envelope initiated" },
    { state: "STORED", label: "Stored in MinIO", desc: "Object written, awaits scanning" },
    { state: "READY", label: "Ready for Processing", desc: "Antivirus scan passed" },
  ];

  return (
    <div className="border rounded-lg bg-surface p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b pb-3">
        <div>
          <h4 className="font-serif font-semibold text-secondary text-sm flex items-center gap-2">
            <ShieldCheck className="size-4 text-[var(--ci-teal-700)]" />
            Evidence Security & Ingestion Pipeline (BG-004)
          </h4>
          <p className="text-xs font-serif text-muted-foreground mt-0.5">
            Strict quarantine gating: unprocessed binary evidence cannot be fed to downstream extractors without verified scan.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-serif">
        {steps.map((step, idx) => {
          const isActive = currentState === step.state;
          return (
            <div
              key={step.state}
              className={`p-3 rounded border transition-colors ${
                isActive
                  ? "border-[var(--status-info)] bg-[var(--status-info-surface)]"
                  : "border-slate-200 bg-slate-50/50"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-secondary">{step.label}</span>
                <span className="text-[10px] font-mono text-muted-foreground">0{idx + 1}</span>
              </div>
              <p className="text-muted-foreground text-[11px] leading-relaxed">{step.desc}</p>
            </div>
          );
        })}
      </div>

      <div className="rounded bg-amber-50 border border-amber-200 p-3 text-xs font-serif text-amber-900 flex items-start gap-2">
        <Lock className="size-3.5 text-amber-700 mt-0.5 shrink-0" />
        <p>
          <span className="font-semibold">Scanner Gate (BG-004):</span> Currently running <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">NoOpScanner</code>. Files remain in <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">STORED</code> state and will not automatically transition to <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">READY</code> until external ClamAV/scanner webhook is configured.
        </p>
      </div>
    </div>
  );
}
