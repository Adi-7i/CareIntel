"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Clock, ShieldCheck, Activity, FileText, BrainCircuit, Info, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";

interface CaseDetailsProps {
  caseId: string;
}

export function CaseDetails({ caseId }: CaseDetailsProps) {
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Area */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div className="flex items-center gap-4">
          <Button render={<Link href="/cases" />} variant="outline" size="icon" aria-label="Back to cases">
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="font-serif text-2xl font-semibold tracking-tight text-secondary">
                Case Workspace
              </h1>
              <Badge variant="outline" className="font-mono text-xs font-serif bg-slate-100 text-slate-800">
                {caseId}
              </Badge>
              <Badge variant="outline" className="font-serif text-xs bg-amber-50 text-amber-800 border-amber-300">
                Live State Unloaded (BG-002)
              </Badge>
            </div>
            <p className="font-serif text-xs text-muted-foreground mt-1">
              Case record detail view for qualified clinical review and workspace orchestration.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" render={<Link href={`/cases/${caseId}/intelligence`} />}>
            <BrainCircuit className="mr-1.5 size-3.5" />
            Intelligence
          </Button>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex border-b text-sm font-serif overflow-x-auto gap-2">
        <Link
          href={`/cases/${caseId}`}
          className="border-b-2 border-[var(--ci-teal-700)] text-[var(--ci-teal-700)] font-semibold px-4 py-2 flex items-center gap-1.5 whitespace-nowrap"
        >
          <Activity className="size-4" />
          Overview
        </Link>
        <Link
          href={`/cases/${caseId}/consent`}
          className="border-b-2 border-transparent text-muted-foreground hover:text-secondary px-4 py-2 flex items-center gap-1.5 whitespace-nowrap transition-colors"
        >
          <ShieldCheck className="size-4" />
          Consent Panel
        </Link>
        <Link
          href={`/cases/${caseId}/intake`}
          className="border-b-2 border-transparent text-muted-foreground hover:text-secondary px-4 py-2 flex items-center gap-1.5 whitespace-nowrap transition-colors"
        >
          <Clock className="size-4" />
          Intake & Encounters
        </Link>
        <Link
          href={`/cases/${caseId}/evidence`}
          className="border-b-2 border-transparent text-muted-foreground hover:text-secondary px-4 py-2 flex items-center gap-1.5 whitespace-nowrap transition-colors"
        >
          <FileText className="size-4" />
          Evidence & Processing
        </Link>
        <Link
          href={`/cases/${caseId}/intelligence`}
          className="border-b-2 border-transparent text-muted-foreground hover:text-secondary px-4 py-2 flex items-center gap-1.5 whitespace-nowrap transition-colors"
        >
          <BrainCircuit className="size-4" />
          Clinical Intelligence
        </Link>
      </div>

      {/* Blocker Notice */}
      <div className="rounded-md bg-slate-50 border border-slate-200 p-4 text-xs font-serif text-slate-700 space-y-1">
        <div className="flex items-center gap-2 font-semibold text-secondary">
          <Info className="size-4 text-[var(--ci-teal-700)] shrink-0" />
          <span>Case Data Persistence Boundary (BG-002, requirement.md §6)</span>
        </div>
        <p>
          Target Case ID: <code className="bg-slate-200 px-1 py-0.5 rounded font-mono text-secondary">{caseId}</code>. In frontend-only execution, live retrieval from <code className="bg-slate-200 px-1 py-0.5 rounded">GET /api/v1/cases/{`{id}`}</code> is disabled to prevent mock hallucination. Contract fields and sub-routes are structured for instant binding.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Workspace (Left Column) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contract Schema Overview */}
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
              <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
                <Activity className="size-4" />
                Case Schema Specification (CaseResponse)
              </h2>
              <span className="text-xs font-mono text-muted-foreground">Contract Version 1</span>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-serif">
                <div className="p-3 rounded border bg-slate-50/50 space-y-1">
                  <span className="text-muted-foreground">Case Identifier (case_id)</span>
                  <p className="font-mono font-medium text-secondary truncate">{caseId}</p>
                </div>
                <div className="p-3 rounded border bg-slate-50/50 space-y-1">
                  <span className="text-muted-foreground">Synthetic Subject ID</span>
                  <p className="font-mono text-muted-foreground italic">Pending API read (BG-001)</p>
                </div>
                <div className="p-3 rounded border bg-slate-50/50 space-y-1">
                  <span className="text-muted-foreground">Case State</span>
                  <p className="font-mono text-muted-foreground italic">CREATED (initial) | Pending read</p>
                </div>
                <div className="p-3 rounded border bg-slate-50/50 space-y-1">
                  <span className="text-muted-foreground">Record Version</span>
                  <p className="font-mono text-muted-foreground italic">1</p>
                </div>
                <div className="p-3 rounded border bg-slate-50/50 space-y-1">
                  <span className="text-muted-foreground">Facility ID (facility_id)</span>
                  <p className="font-mono text-muted-foreground italic">Unassigned (Optional)</p>
                </div>
                <div className="p-3 rounded border bg-slate-50/50 space-y-1">
                  <span className="text-muted-foreground">Clinical Priority</span>
                  <p className="font-serif text-secondary font-medium">Unassigned (Reviewer evaluated)</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Sub-Route Navigation Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="border rounded-lg bg-surface p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
                  <Clock className="size-4 text-[var(--ci-teal-700)]" />
                  Intake & Encounters
                </h3>
                <Link href={`/cases/${caseId}/intake`} className="text-xs text-[var(--ci-teal-700)] hover:underline flex items-center gap-1">
                  Open <ExternalLink className="size-3" />
                </Link>
              </div>
              <p className="text-xs font-serif text-muted-foreground">
                Document clinical encounters and narrative text intakes for this case.
              </p>
            </div>

            <div className="border rounded-lg bg-surface p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
                  <FileText className="size-4 text-[var(--ci-teal-700)]" />
                  Evidence Workspace
                </h3>
                <Link href={`/cases/${caseId}/evidence`} className="text-xs text-[var(--ci-teal-700)] hover:underline flex items-center gap-1">
                  Open <ExternalLink className="size-3" />
                </Link>
              </div>
              <p className="text-xs font-serif text-muted-foreground">
                Upload multimodal evidence, view processing runs, and monitor OCR / normalization pipelines.
              </p>
            </div>
          </div>
        </div>

        {/* Context Column (Right Column) */}
        <div className="space-y-6">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b flex items-center justify-between">
              <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
                <ShieldCheck className="size-4 text-[var(--ci-teal-700)]" />
                Consent Posture
              </h2>
              <Link href={`/cases/${caseId}/consent`} className="text-xs text-[var(--ci-teal-700)] hover:underline">
                Manage
              </Link>
            </div>
            <div className="p-6">
              <EmptyState
                icon={<ShieldCheck className="size-8 text-muted-foreground" />}
                title="Consent Unbound"
                description="Subject consent must be verified via the consent panel before downstream AI operations."
              />
            </div>
          </div>

          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
                <BrainCircuit className="size-4 text-[var(--ci-teal-700)]" />
                Advisory Status
              </h2>
            </div>
            <div className="p-6">
              <EmptyState
                icon={<BrainCircuit className="size-8 text-muted-foreground" />}
                title="Evaluation Not Executed"
                description="Clinical structuring, timelines, and conflicts evaluate when evidence is in READY state."
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
