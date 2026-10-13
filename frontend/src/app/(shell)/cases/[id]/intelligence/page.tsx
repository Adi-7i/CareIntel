import * as React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EvaluationTrigger } from "@/components/intelligence/evaluation-trigger";
import { StructuringSummaryCard } from "@/components/intelligence/structuring-summary-card";
import { TimelineList } from "@/components/intelligence/timeline-list";
import { ConflictList } from "@/components/intelligence/conflict-list";
import { MissingInfoList } from "@/components/intelligence/missing-info-list";
import { RetrievalForm } from "@/components/intelligence/retrieval-form";
import { AIDraftForm } from "@/components/intelligence/ai-draft-form";

export const metadata: Metadata = {
  title: "Case Intelligence | CareIntel",
  description: "Clinical intelligence workspace for temporal structuring, conflicts, and advisory drafts",
};

interface CaseIntelligencePageProps {
  params: Promise<{ id: string }>;
}

export default async function CaseIntelligencePage({ params }: CaseIntelligencePageProps) {
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
                Case Clinical Intelligence Workspace
              </h1>
              <Badge variant="outline" className="font-mono text-xs font-serif bg-slate-100 text-slate-800">
                Case {id}
              </Badge>
              <Badge variant="outline" className="font-serif text-xs bg-amber-50 text-amber-800 border-amber-300">
                Advisory Only
              </Badge>
            </div>
            <p className="font-serif text-xs text-muted-foreground mt-1">
              AI-generated advisory drafts, temporal structuring, and conflict analysis for qualified reviewer assessment (FE-014–017).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" render={<Link href={`/cases/${id}`} />}>
            Back to Case
          </Button>
        </div>
      </div>

      {/* Sub-Navigation Tabs within Intelligence */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeline">Chronological Timeline</TabsTrigger>
          <TabsTrigger value="conflicts">Conflicts Ledger</TabsTrigger>
          <TabsTrigger value="missing">Missing Information</TabsTrigger>
          <TabsTrigger value="retrieval">Guideline Retrieval</TabsTrigger>
          <TabsTrigger value="drafts">AI Advisory Drafts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary text-sm">
                Dispatch Structuring Evaluation for Case
              </h2>
            </div>
            <div className="p-6">
              <EvaluationTrigger />
            </div>
          </div>

          <StructuringSummaryCard />
        </TabsContent>

        <TabsContent value="timeline">
          <TimelineList caseId={id} />
        </TabsContent>

        <TabsContent value="conflicts">
          <ConflictList caseId={id} />
        </TabsContent>

        <TabsContent value="missing">
          <MissingInfoList caseId={id} />
        </TabsContent>

        <TabsContent value="retrieval">
          <RetrievalForm caseId={id} />
        </TabsContent>

        <TabsContent value="drafts">
          <AIDraftForm caseId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
