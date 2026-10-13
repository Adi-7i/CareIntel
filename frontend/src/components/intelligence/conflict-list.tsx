"use client";

import * as React from "react";
import { AlertTriangle, Info, CheckCircle2, XCircle } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { ClinicalConflict, ConflictStatus } from "@/types";

interface ConflictListProps {
  caseId?: string;
  conflicts?: ClinicalConflict[];
}

function ConflictStatusBadge({ status }: { status: ConflictStatus }) {
  switch (status) {
    case "RESOLVED":
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]">
          <CheckCircle2 className="mr-1 size-3" /> RESOLVED
        </Badge>
      );
    case "DISMISSED":
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-slate-100 text-slate-600 border-slate-300">
          <XCircle className="mr-1 size-3" /> DISMISSED
        </Badge>
      );
    case "UNRESOLVED":
    default:
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]">
          <AlertTriangle className="mr-1 size-3" /> UNRESOLVED
        </Badge>
      );
  }
}

export function ConflictList({ caseId, conflicts = [] }: ConflictListProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-md bg-slate-50 border border-slate-200 p-4 text-xs font-serif text-slate-700 space-y-1">
        <div className="flex items-center gap-2 font-semibold text-secondary">
          <Info className="size-4 text-[var(--ci-teal-700)] shrink-0" />
          <span>Cross-Evidence Conflict Detection Scope (BG-007, requirement.md §6)</span>
        </div>
        <p>
          Conflict detection identifies contradictions between distinct evidence items (e.g., mismatched symptom onset dates or divergent vital readings). Automated severity ranking and manual resolution actions are pending backend schema expansion.
        </p>
      </div>

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <AlertTriangle className="size-4 text-amber-600" />
            Conflicting Information Ledger (FE-014)
          </h2>
          {caseId && (
            <span className="text-xs font-mono text-muted-foreground">Case {caseId}</span>
          )}
        </div>

        {conflicts.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<AlertTriangle className="size-8 text-amber-500" />}
              title="Conflicts Not Yet Evaluated"
              description="Cross-evidence conflict evaluation has not been executed for this case. Evaluation requires multiple ingested evidence items in READY state and completed candidate extraction runs (BG-007)."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30 text-xs">
                <TableHead className="font-serif font-semibold text-secondary w-[160px]">Field / Topic</TableHead>
                <TableHead className="font-serif font-semibold text-secondary">Conflict Description</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[130px]">Status</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[180px]">Conflicting Evidence IDs</TableHead>
                <TableHead className="font-serif font-semibold text-secondary text-right w-[140px]">Detected At</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {conflicts.map((conflict) => (
                <TableRow key={conflict.conflict_id} className="text-xs font-serif">
                  <TableCell className="font-mono font-medium text-secondary">{conflict.field_name}</TableCell>
                  <TableCell className="text-slate-800">{conflict.description}</TableCell>
                  <TableCell>
                    <ConflictStatusBadge status={conflict.status} />
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {conflict.conflicting_evidence_ids.join(", ")}
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground font-mono">
                    {conflict.detected_at || "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
