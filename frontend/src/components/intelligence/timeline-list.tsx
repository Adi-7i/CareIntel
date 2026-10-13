"use client";

import * as React from "react";
import { Clock, Info } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { TimelineEvent, TemporalPrecision } from "@/types";

interface TimelineListProps {
  caseId?: string;
  events?: TimelineEvent[];
}

function PrecisionBadge({ precision }: { precision: TemporalPrecision }) {
  let color = "bg-slate-100 text-slate-700 border-slate-300";
  if (precision === "EXACT") color = "bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]";
  else if (precision === "DATE_ONLY") color = "bg-[var(--status-info-surface)] text-[var(--status-info-text)] border-[var(--status-info)]";
  else if (precision === "APPROXIMATE") color = "bg-[var(--status-warning-surface)] text-[var(--status-warning-text)] border-[var(--status-warning)]";
  else if (precision === "UNKNOWN") color = "bg-amber-100 text-amber-900 border-amber-300";

  return (
    <Badge variant="outline" className={`font-mono text-[10px] uppercase font-semibold ${color}`}>
      {precision}
    </Badge>
  );
}

export function TimelineList({ caseId, events = [] }: TimelineListProps) {
  return (
    <div className="space-y-6">
      {/* Temporal Ordering Rule Notice */}
      <div className="rounded-md bg-slate-50 border border-slate-200 p-4 text-xs font-serif text-slate-700 space-y-1">
        <div className="flex items-center gap-2 font-semibold text-secondary">
          <Info className="size-4 text-[var(--ci-teal-700)] shrink-0" />
          <span>Temporal Structuring & Ordering Protocol (DEC-05, requirement.md §6)</span>
        </div>
        <p>
          Clinical timeline events are normalized into ISO-8601 interval bounds. Crucially, events with <span className="font-semibold text-secondary">UNKNOWN</span> temporal expressions are <span className="underline">never</span> silently sorted into chronological slots — they are preserved in a distinct unanchored section to prevent clinical misinterpretation.
        </p>
      </div>

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <Clock className="size-4 text-[var(--ci-teal-700)]" />
            Clinical Chronology & Temporal Ledger (FE-014)
          </h2>
          {caseId && (
            <span className="text-xs font-mono text-muted-foreground">Case {caseId}</span>
          )}
        </div>

        {events.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<Clock className="size-8 text-muted-foreground" />}
              title="Timeline Requires Completed Structuring Evaluation (BG-006/007)"
              description="Clinical structuring has not yet processed normalized evidence for this case. Timeline events will be displayed once the candidate extraction and temporal normalizer run concludes."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30 text-xs">
                <TableHead className="font-serif font-semibold text-secondary w-[220px]">Source Statement</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[130px]">Event Type</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[160px]">Raw Expression</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[110px]">Precision</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[180px]">Normalized Bounds</TableHead>
                <TableHead className="font-serif font-semibold text-secondary text-right w-[110px]">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.map((ev) => (
                <TableRow key={ev.event_id} className="text-xs font-serif">
                  <TableCell className="text-slate-800 font-medium">{ev.source_statement}</TableCell>
                  <TableCell className="font-mono text-secondary">{ev.event_type}</TableCell>
                  <TableCell className="text-muted-foreground">{ev.raw_temporal_expression || "—"}</TableCell>
                  <TableCell>
                    <PrecisionBadge precision={ev.precision} />
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {ev.normalized_date_bounds?.start
                      ? `${ev.normalized_date_bounds.start} → ${ev.normalized_date_bounds.end || "Open"}`
                      : ev.resolution || "Unresolved"}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    <Badge variant="outline" className="text-[10px]">
                      {ev.status}
                    </Badge>
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
