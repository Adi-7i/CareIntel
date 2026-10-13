import * as React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FileEvidenceForm } from "@/components/evidence/file-evidence-form";
import { TextEvidenceForm } from "@/components/evidence/text-evidence-form";
import { EvidenceList } from "@/components/evidence/evidence-list";
import { EvidenceStateIndicator } from "@/components/evidence/evidence-state-indicator";
import { EvidencePreviewPanel } from "@/components/evidence/evidence-preview-panel";

export const metadata: Metadata = {
  title: "Case Evidence | CareIntel",
  description: "Ingest and inspect multimodal clinical evidence records",
};

interface CaseEvidencePageProps {
  params: Promise<{ id: string }>;
}

export default async function CaseEvidencePage({ params }: CaseEvidencePageProps) {
  const { id } = await params;

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div className="flex items-center gap-4">
          <Button render={<Link href={`/cases/${id}`} />} variant="outline" size="icon" aria-label="Back to case">
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="font-serif text-2xl font-semibold tracking-tight text-secondary">
                Evidence Workspace
              </h1>
              <Badge variant="outline" className="font-mono text-xs font-serif bg-slate-100 text-slate-800">
                Case {id}
              </Badge>
            </div>
            <p className="font-serif text-xs text-muted-foreground mt-1">
              Ingest, inspect, and track multimodal medical records, audio dictations, and clinical text (FE-008–010).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" render={<Link href="/evidence" />}>
            <Cpu className="mr-1.5 size-3.5" />
            Global Processing Hub
          </Button>
        </div>
      </div>

      {/* Security Pipeline Indicator */}
      <EvidenceStateIndicator currentState="STORED" />

      {/* Upload Forms Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <div className="border rounded-lg bg-surface p-6 shadow-sm space-y-4">
          <h2 className="font-serif font-semibold text-secondary text-base">
            Upload Binary Evidence File
          </h2>
          <FileEvidenceForm caseId={id} />
        </div>

        <div className="border rounded-lg bg-surface p-6 shadow-sm space-y-4">
          <h2 className="font-serif font-semibold text-secondary text-base">
            Register Direct Clinical Text
          </h2>
          <TextEvidenceForm caseId={id} />
        </div>
      </div>

      {/* Evidence Ledger & Details */}
      <div className="space-y-6">
        <EvidenceList caseId={id} />
        <EvidencePreviewPanel />
      </div>
    </div>
  );
}
