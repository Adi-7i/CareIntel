"use client";

import * as React from "react";
import { FileText, Search, Info } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";
import { ModalityIcon } from "./modality-icon";
import { EvidenceStateBadge } from "./evidence-state-badge";
import type { EvidenceResponse } from "@/types";

interface EvidenceListProps {
  caseId: string;
  items?: EvidenceResponse[];
  onSelectEvidence?: (evidence: EvidenceResponse) => void;
}

export function EvidenceList({ caseId, items = [], onSelectEvidence }: EvidenceListProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-serif font-semibold text-secondary text-base flex items-center gap-2">
            <FileText className="size-4 text-[var(--ci-teal-700)]" />
            Case Evidence Ledger (EvidenceResponse)
          </h3>
          <p className="text-xs font-serif text-muted-foreground mt-0.5">
            Multimodal evidence envelopes registered under Case {caseId}.
          </p>
        </div>
      </div>

      {/* Blocker Notice */}
      <div className="rounded-md bg-amber-50 border border-amber-200 p-3.5 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold">
          <Info className="size-3.5 text-amber-700 shrink-0" />
          <span>Evidence List Route Registration (BG-005)</span>
        </div>
        <p>
          The endpoint <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">GET /api/v1/cases/{`{id}`}/evidence</code> is not registered on the backend router. Ingested items are queryable by individual UUID (<code className="bg-amber-100 px-1 py-0.5 rounded font-mono">GET /api/v1/evidence/{`{id}`}</code>). When connected, this ledger renders all 12 contract fields.
        </p>
      </div>

      {/* Data Table */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30 text-xs">
              <TableHead className="font-serif font-semibold text-secondary w-[180px]">Filename / Identifier</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[110px]">Modality</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[130px]">State</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[140px]">Content Type</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[90px]">Size</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[90px]">Language</TableHead>
              <TableHead className="font-serif font-semibold text-secondary text-right w-[140px]">Uploaded At</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-44">
                  <EmptyState
                    icon={<Search className="size-7 text-muted-foreground" />}
                    title="No Evidence Ingested"
                    description="Upload file evidence or register narrative notes to populate this evidence roster."
                  />
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.evidence_id}
                  className="cursor-pointer hover:bg-muted/40 text-xs font-serif"
                  onClick={() => onSelectEvidence?.(item)}
                >
                  <TableCell className="font-medium text-secondary truncate">{item.original_filename}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <ModalityIcon modality={item.modality} />
                      <span className="uppercase text-[11px] font-mono">{item.modality}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <EvidenceStateBadge state={item.state} />
                  </TableCell>
                  <TableCell className="font-mono text-muted-foreground">{item.content_type}</TableCell>
                  <TableCell className="font-mono">{(item.size_bytes / 1024 / 1024).toFixed(2)} MB</TableCell>
                  <TableCell className="font-mono">{item.source_language || "—"}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{item.created_at}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
