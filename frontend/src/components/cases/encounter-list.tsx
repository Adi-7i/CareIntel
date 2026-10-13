"use client";

import * as React from "react";
import { Clock, Info } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface EncounterListProps {
  caseId: string;
}

export function EncounterList({ caseId }: EncounterListProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-serif font-semibold text-secondary text-base flex items-center gap-2">
            <Clock className="size-4 text-[var(--ci-teal-700)]" />
            Encounter History
          </h3>
          <p className="text-xs font-serif text-muted-foreground mt-0.5">
            Documented clinical encounters associated with Case {caseId}.
          </p>
        </div>
      </div>

      <div className="rounded-md bg-amber-50 border border-amber-200 p-3 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold">
          <Info className="size-3.5 text-amber-700 shrink-0" />
          <span>Encounter Query API Status (BG-005)</span>
        </div>
        <p>
          The endpoint to list encounters for a case (<code className="bg-amber-100 px-1 py-0.5 rounded">GET /api/v1/cases/{`{id}`}/encounters</code>) is pending backend router registration. Logged encounters will appear in this ledger once connected.
        </p>
      </div>

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead className="font-serif font-semibold text-secondary w-[200px]">Encounter ID</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[180px]">Type</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[180px]">Occurred At</TableHead>
              <TableHead className="font-serif font-semibold text-secondary">Notes</TableHead>
              <TableHead className="font-serif font-semibold text-secondary text-right w-[140px]">Recorded</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell colSpan={5} className="h-44">
                <EmptyState
                  icon={<Clock className="size-7 text-muted-foreground" />}
                  title="No Encounters Logged"
                  description="No clinical encounters have been recorded for this case yet. Use the form above to log an encounter."
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
