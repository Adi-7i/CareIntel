import * as React from "react";
import type { Metadata } from "next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EvaluationTrigger } from "@/components/intelligence/evaluation-trigger";
import { StructuringSummaryCard } from "@/components/intelligence/structuring-summary-card";
import { TimelineList } from "@/components/intelligence/timeline-list";
import { ConflictList } from "@/components/intelligence/conflict-list";
import { MissingInfoList } from "@/components/intelligence/missing-info-list";
import { RetrievalForm } from "@/components/intelligence/retrieval-form";
import { AIDraftForm } from "@/components/intelligence/ai-draft-form";

export const metadata: Metadata = {
  title: "Clinical Intelligence Workspace | CareIntel",
  description: "View and manage clinical structured information and AI advisory drafts.",
};

export default function IntelligencePage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      <header>
        <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">
          Clinical Intelligence
        </h1>
        <p className="mt-1 font-serif text-sm text-muted-foreground">
          View structured clinical facts, timelines, and verified AI advisory drafts.
        </p>
      </header>
      
      <div className="rounded-md bg-muted/40 border p-4 mb-6">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          System Integration Notice
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          This workspace is prepared for backend integration. Forms and triggers will validate locally but require an active session and connected backend services to return real clinical data.
        </p>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="conflicts">Conflicts</TabsTrigger>
          <TabsTrigger value="missing">Missing Info & Questions</TabsTrigger>
          <TabsTrigger value="retrieval">Retrieval</TabsTrigger>
          <TabsTrigger value="drafts">AI Drafts</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Trigger Evaluation</h2>
            </div>
            <div className="p-6">
              <EvaluationTrigger />
            </div>
          </div>
          
          <StructuringSummaryCard />
        </TabsContent>
        
        <TabsContent value="timeline">
          <TimelineList />
        </TabsContent>
        
        <TabsContent value="conflicts">
          <ConflictList />
        </TabsContent>
        
        <TabsContent value="missing">
          <MissingInfoList />
        </TabsContent>

        <TabsContent value="retrieval">
          <RetrievalForm />
        </TabsContent>

        <TabsContent value="drafts">
          <AIDraftForm />
        </TabsContent>
      </Tabs>
    </div>
  );
}
