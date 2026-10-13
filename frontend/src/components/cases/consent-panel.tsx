"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, ShieldCheck, AlertCircle, Info, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { ConsentPurpose } from "@/types";

interface ConsentPanelProps {
  caseId: string;
}

interface PurposeDefinition {
  purpose: ConsentPurpose;
  title: string;
  description: string;
  requiredFor: string;
  defaultNoticeVersion: string;
}

const PURPOSES: PurposeDefinition[] = [
  {
    purpose: "data_processing",
    title: "Data Processing (Core Ingestion & Structuring)",
    description: "Authorization to ingest, store, normalize, and extract clinical candidate fields from multimodal case evidence.",
    requiredFor: "Mandatory for evidence processing and normalization",
    defaultNoticeVersion: "1.0",
  },
  {
    purpose: "ai_analysis",
    title: "AI Analysis & Advisory Synthesis",
    description: "Authorization to perform automated temporal analysis, cross-evidence conflict detection, guideline retrieval, and generate advisory drafts.",
    requiredFor: "Mandatory for Clinical Intelligence evaluation & draft generation",
    defaultNoticeVersion: "1.0",
  },
  {
    purpose: "referral",
    title: "Clinical Referral & Escalation Routing",
    description: "Authorization to route structured summaries and case dossiers to external specialists or emergency care networks.",
    requiredFor: "Mandatory for cross-facility referral and escalation actions",
    defaultNoticeVersion: "1.0",
  },
];

export function ConsentPanel({ caseId }: ConsentPanelProps) {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 border-b pb-4">
        <Button render={<Link href={`/cases/${caseId}`} />} variant="outline" size="icon" aria-label="Back to case">
          <ArrowLeft className="size-4" />
        </Button>
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-serif text-2xl font-semibold tracking-tight text-secondary">
              Consent Management Panel
            </h1>
            <Badge variant="outline" className="font-mono text-xs font-serif bg-slate-100 text-slate-800">
              Case {caseId}
            </Badge>
          </div>
          <p className="font-serif text-xs text-muted-foreground mt-1">
            Track and verify explicit subject consent purposes and notice versions (FE-006, requirement.md §6).
          </p>
        </div>
      </div>

      {/* Advisory & Blocker Notices */}
      <div className="space-y-3">
        <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-xs font-serif text-amber-900 space-y-1">
          <div className="flex items-center gap-2 font-semibold">
            <AlertCircle className="size-4 text-amber-700 shrink-0" />
            <span>Consent Operations Unavailable in Frontend-Only Mode (BG-003)</span>
          </div>
          <p>
            Backend consent query and modification endpoints (<code className="bg-amber-100 px-1 py-0.5 rounded">GET /api/v1/consents/{`{id}`}</code>, <code className="bg-amber-100 px-1 py-0.5 rounded">POST /api/v1/consents</code>) are not connected. All consent states shown below represent required governance structures. No simulated checkboxes or fake active states are permitted.
          </p>
        </div>

        <div className="rounded-md bg-slate-50 border border-slate-200 p-4 text-xs font-serif text-slate-700 space-y-1">
          <div className="flex items-center gap-2 font-semibold text-secondary">
            <Info className="size-4 text-[var(--ci-teal-700)] shrink-0" />
            <span>Approved Advisory Disclosure & Non-Diagnostic Notice</span>
          </div>
          <p>
            CareIntel operates exclusively on synthetic or de-identified subject cohorts. All downstream processing and AI-assisted summaries are purely advisory drafts for qualified clinical reviewers and must never supersede clinical judgment.
          </p>
        </div>
      </div>

      {/* Consent Lifecycle Visualization */}
      <div className="border rounded-lg bg-surface p-6 shadow-sm space-y-4">
        <h2 className="font-serif font-semibold text-secondary text-sm flex items-center gap-2">
          <ShieldCheck className="size-4 text-[var(--ci-teal-700)]" />
          Consent Lifecycle State Machine
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-serif">
          <div className="p-3 rounded border border-slate-200 bg-slate-50/50 space-y-1">
            <span className="font-semibold text-slate-800">1. REQUESTED</span>
            <p className="text-muted-foreground">Notice presented to subject or guardian; awaiting formal capture.</p>
          </div>
          <div className="p-3 rounded border border-[var(--status-info)] bg-[var(--status-info-surface)] space-y-1">
            <span className="font-semibold text-[var(--status-info-text)]">2. ACTIVE</span>
            <p className="text-[var(--status-info-text)]">Explicit authorization captured under specified notice version.</p>
          </div>
          <div className="p-3 rounded border border-amber-300 bg-amber-50/50 space-y-1">
            <span className="font-semibold text-amber-900">3. WITHDRAWN</span>
            <p className="text-amber-800">Subject has revoked consent; halts further processing pipelines.</p>
          </div>
          <div className="p-3 rounded border border-slate-200 bg-slate-50/50 space-y-1">
            <span className="font-semibold text-slate-800">4. EXPIRED / STALE</span>
            <p className="text-muted-foreground">Notice version deprecated or superseded by updated terms.</p>
          </div>
        </div>
      </div>

      {/* Purpose Panels */}
      <div className="space-y-4">
        <h2 className="font-serif font-semibold text-secondary text-base">
          Mandatory Consent Purposes (Notice Version 1.0)
        </h2>

        <div className="grid gap-4">
          {PURPOSES.map((item) => (
            <div key={item.purpose} className="border rounded-lg bg-surface p-5 shadow-sm space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-serif font-semibold text-secondary text-sm">{item.title}</h3>
                    <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-700 font-mono">
                      {item.purpose}
                    </code>
                  </div>
                  <p className="text-xs font-serif text-muted-foreground">{item.description}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant="outline" className="font-mono text-xs font-serif bg-slate-100">
                    Notice v{item.defaultNoticeVersion}
                  </Badge>
                  <Badge variant="outline" className="font-serif text-xs bg-slate-100 text-slate-600 border-slate-300">
                    State: Disconnected
                  </Badge>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-serif">
                <span className="text-muted-foreground italic">
                  Governance Rule: {item.requiredFor}
                </span>

                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" disabled className="text-xs cursor-not-allowed">
                    <Lock className="mr-1.5 size-3" />
                    Capture Consent (BG-003)
                  </Button>
                  <Button variant="ghost" size="sm" disabled className="text-xs text-destructive cursor-not-allowed">
                    Withdraw (BG-003)
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex items-center justify-between border-t pt-4 text-xs font-serif text-muted-foreground">
        <span>CareIntel Consent Verification Protocol • Governed by DEC-03 and BG-003</span>
        <Button variant="outline" size="sm" render={<Link href={`/cases/${caseId}`} />}>
          Return to Case
        </Button>
      </div>
    </div>
  );
}
