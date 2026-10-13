import * as React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EncounterForm } from "@/components/cases/encounter-form";
import { EncounterList } from "@/components/cases/encounter-list";
import { NarrativeForm } from "@/components/cases/narrative-form";

export const metadata: Metadata = {
  title: "Case Intake & Encounters | CareIntel",
  description: "Record encounters and ingest clinical narrative notes",
};

interface CaseIntakePageProps {
  params: Promise<{ id: string }>;
}

export default async function CaseIntakePage({ params }: CaseIntakePageProps) {
  const { id } = await params;

  return (
    <div className="space-y-6 max-w-5xl mx-auto py-2">
      {/* Header */}
      <div className="flex items-center gap-4 border-b pb-4">
        <Button render={<Link href={`/cases/${id}`} />} variant="outline" size="icon" aria-label="Back to case">
          <ArrowLeft className="size-4" />
        </Button>
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-serif text-2xl font-semibold tracking-tight text-secondary">
              Intake & Encounters Workspace
            </h1>
            <Badge variant="outline" className="font-mono text-xs font-serif bg-slate-100 text-slate-800">
              Case {id}
            </Badge>
          </div>
          <p className="font-serif text-xs text-muted-foreground mt-1">
            Capture clinical interactions, timeline markers, and free-text narrative observations (FE-005, FE-007).
          </p>
        </div>
      </div>

      {/* Forms & History Grid */}
      <div className="space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <EncounterForm caseId={id} />
          <NarrativeForm caseId={id} />
        </div>

        <EncounterList caseId={id} />
      </div>
    </div>
  );
}
