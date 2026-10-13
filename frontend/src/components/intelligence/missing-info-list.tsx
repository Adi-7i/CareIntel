"use client";

import * as React from "react";
import { FileQuestion, HelpCircle, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { MissingInfoItem, MissingInfoCategory } from "@/types";

interface MissingInfoListProps {
  caseId?: string;
  items?: MissingInfoItem[];
}

function CategoryBadge({ category }: { category: MissingInfoCategory }) {
  let color = "bg-slate-100 text-slate-700 border-slate-300";
  if (category === "MISSING") color = "bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]";
  else if (category === "CONFLICTING") color = "bg-amber-100 text-amber-900 border-amber-300";
  else if (category === "UNREADABLE") color = "bg-purple-50 text-purple-800 border-purple-300";
  else if (category === "UNVERIFIED") color = "bg-[var(--status-warning-surface)] text-[var(--status-warning-text)] border-[var(--status-warning)]";
  else if (category === "SATISFIED") color = "bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]";

  return (
    <Badge variant="outline" className={`font-mono text-[10px] uppercase font-semibold ${color}`}>
      {category}
    </Badge>
  );
}

export function MissingInfoList({ caseId, items = [] }: MissingInfoListProps) {
  return (
    <div className="space-y-8">
      {/* Blocker & Protocol Notice */}
      <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-semibold">
          <Info className="size-4 text-amber-700 shrink-0" />
          <span>Clarification & Questionnaire API Gate (BG-008, requirement.md §6)</span>
        </div>
        <p>
          Follow-up clarification questions are generated to address missing or unreadable evidence requirements (bounded to max 3 questions/round, max 2 rounds). However, endpoints to answer questions, stop questioning, or return to intake (<code className="bg-amber-100 px-1 py-0.5 rounded font-mono">POST /api/v1/cases/{`{id}`}/clarifications/answer</code>) are unregistered. All questions are rendered in <span className="font-semibold">display-only mode</span> for clinical reviewer reference.
        </p>
      </div>

      {/* Section 1: Missing Checklist Requirements */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <FileQuestion className="size-4 text-[var(--ci-teal-700)]" />
            Missing Information Checklist Requirements (FE-015)
          </h2>
          {caseId && (
            <span className="text-xs font-mono text-muted-foreground">Case {caseId}</span>
          )}
        </div>

        {items.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<FileQuestion className="size-8 text-muted-foreground" />}
              title="Missing Information Not Yet Evaluated"
              description="Clinical gap analysis has not yet evaluated case requirements. Requirements evaluate across MISSING, CONFLICTING, UNREADABLE, and UNVERIFIED categories once evidence is processed."
            />
          </div>
        ) : (
          <div className="p-6 space-y-3">
            {items.map((item) => (
              <div key={item.item_id} className="p-4 rounded border bg-slate-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CategoryBadge category={item.category} />
                    {item.is_blocking && (
                      <Badge variant="outline" className="font-serif text-[10px] bg-red-50 text-red-700 border-red-300">
                        Blocking Intake
                      </Badge>
                    )}
                  </div>
                  <span className="text-[11px] font-mono text-muted-foreground">
                    Round {item.round_number}
                  </span>
                </div>
                <p className="font-serif text-sm text-secondary font-medium">{item.question_prompt}</p>
                <p className="font-serif text-xs text-muted-foreground">{item.clinical_rationale}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 2: Clarification Questions (Display-Only) */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <HelpCircle className="size-4 text-[var(--ci-teal-700)]" />
            Advisory Clarification Inquiries (Display Only — BG-008)
          </h2>
          <Badge variant="outline" className="font-serif text-xs bg-slate-100 text-slate-700">
            Submission Blocked (BG-008)
          </Badge>
        </div>

        <div className="p-6">
          <EmptyState
            icon={<HelpCircle className="size-8 text-muted-foreground" />}
            title="No Active Clarification Questions"
            description="Targeted follow-up inquiries will be populated here when the AI structuring engine detects clinical ambiguities or missing intake data."
          />
        </div>
      </div>
    </div>
  );
}
