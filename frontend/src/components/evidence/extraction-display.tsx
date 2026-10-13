"use client";

import * as React from "react";
import { FileSearch, Info, CheckCircle2, HelpCircle, XCircle } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { ExtractedField, VerificationStatus } from "@/types";

interface ExtractionDisplayProps {
  extractions?: ExtractedField[];
}

function VerificationBadge({ status }: { status: VerificationStatus }) {
  switch (status) {
    case "VERIFIED":
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]">
          <CheckCircle2 className="mr-1 size-3" /> VERIFIED
        </Badge>
      );
    case "REJECTED":
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]">
          <XCircle className="mr-1 size-3" /> REJECTED
        </Badge>
      );
    case "UNVERIFIED":
    default:
      return (
        <Badge variant="outline" className="font-serif text-[11px] bg-[var(--status-warning-surface)] text-[var(--status-warning-text)] border-[var(--status-warning)]">
          <HelpCircle className="mr-1 size-3" /> UNVERIFIED
        </Badge>
      );
  }
}

export function ExtractionDisplay({ extractions = [] }: ExtractionDisplayProps) {
  return (
    <div className="space-y-6">
      {/* Blocker & Scope Notice */}
      <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-semibold">
          <Info className="size-4 text-amber-700 shrink-0" />
          <span>Extraction Architecture Boundaries (BG-006, BG-007, BG-009)</span>
        </div>
        <p>
          Candidate extraction currently relies on demo rules (focused on fever symptoms and ISO-date temporal bounds). Automated cross-evidence conflict synthesis is pending backend pipeline completion (BG-007), and manual clinician field correction endpoints are not yet implemented (BG-009).
        </p>
      </div>

      {/* Confidence Labeling Rule Notice */}
      <div className="rounded-md bg-slate-50 border border-slate-200 p-3 text-xs font-serif text-slate-700">
        <span className="font-semibold text-secondary">Clinical Calibration Notice:</span>{" "}
        Fields with <code className="bg-slate-200 px-1 py-0.5 rounded font-mono">null</code> confidence values are explicitly labeled{" "}
        <span className="font-semibold text-secondary">&ldquo;Unknown&rdquo;</span>, representing uncalibrated model certainty rather than zero certainty.
      </div>

      {/* Extractions Table */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <FileSearch className="size-4 text-[var(--ci-teal-700)]" />
            Extracted Clinical Candidates (FE-013)
          </h2>
          <span className="text-xs font-serif text-muted-foreground">
            {extractions.length} candidate {extractions.length === 1 ? "field" : "fields"}
          </span>
        </div>

        {extractions.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<FileSearch className="size-8 text-muted-foreground" />}
              title="No Candidate Extractions Present"
              description="Execute candidate_extraction processor on normalized evidence to display extracted entities, confidence scores, and provenance."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30 text-xs">
                <TableHead className="font-serif font-semibold text-secondary w-[150px]">Field Type</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[200px]">Raw Value</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[200px]">Normalized Value</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[120px]">Confidence</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[130px]">Verification</TableHead>
                <TableHead className="font-serif font-semibold text-secondary text-right w-[180px]">Provenance</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {extractions.map((field) => (
                <TableRow key={field.field_id} className="text-xs font-serif">
                  <TableCell className="font-mono font-medium text-secondary">{field.field_type}</TableCell>
                  <TableCell className="text-slate-800">{field.raw_value}</TableCell>
                  <TableCell className="text-slate-700">{field.normalized_value || "—"}</TableCell>
                  <TableCell>
                    {field.confidence === null ? (
                      <span className="text-muted-foreground italic">Unknown (Uncalibrated)</span>
                    ) : (
                      <span className="font-mono font-semibold">{(field.confidence * 100).toFixed(1)}%</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <VerificationBadge status={field.verification_status} />
                  </TableCell>
                  <TableCell className="text-right font-mono text-muted-foreground truncate">
                    {field.provenance_evidence_id}
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
