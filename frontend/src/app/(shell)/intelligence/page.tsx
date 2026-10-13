"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EvaluationTrigger } from "@/components/intelligence/evaluation-trigger";
import { StructuringSummaryCard } from "@/components/intelligence/structuring-summary-card";
import { TimelineList } from "@/components/intelligence/timeline-list";
import { ConflictList } from "@/components/intelligence/conflict-list";
import { MissingInfoList } from "@/components/intelligence/missing-info-list";
import { RetrievalForm } from "@/components/intelligence/retrieval-form";
import { AIDraftForm } from "@/components/intelligence/ai-draft-form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, ArrowRight, AlertCircle, Info } from "lucide-react";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default function IntelligencePage() {
  const router = useRouter();
  const [caseLookup, setCaseLookup] = React.useState("");
  const [lookupError, setLookupError] = React.useState("");

  const handleCaseSelect = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = caseLookup.trim();
    if (!trimmed) {
      setLookupError("Please enter a Case UUID.");
      return;
    }
    if (!UUID_REGEX.test(trimmed)) {
      setLookupError("Case ID must be a valid RFC 4122 UUID.");
      return;
    }
    setLookupError("");
    router.push(`/cases/${trimmed}/intelligence`);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">
            Clinical Intelligence Hub
          </h1>
          <p className="mt-1 font-serif text-sm text-muted-foreground">
            AI-generated advisory drafts for qualified reviewer assessment (FE-014–017).
          </p>
        </div>

        {/* Case Context Selector */}
        <form onSubmit={handleCaseSelect} className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
            <Input
              placeholder="Case UUID (open scoped intelligence)..."
              value={caseLookup}
              onChange={(e) => {
                setCaseLookup(e.target.value);
                if (lookupError) setLookupError("");
              }}
              className="pl-8 font-serif text-xs"
              aria-label="Scope to case"
            />
          </div>
          <Button type="submit" variant="secondary" size="sm" className="whitespace-nowrap text-xs">
            Scope Case
            <ArrowRight className="ml-1.5 size-3.5" />
          </Button>
        </form>
      </header>

      {lookupError && (
        <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 -mt-4">
          <AlertCircle className="size-3" /> {lookupError}
        </p>
      )}

      {/* Advisory & Scoping Notice */}
      <div className="rounded-md bg-slate-50 border border-slate-200 p-4 text-xs font-serif text-slate-700 space-y-1">
        <div className="flex items-center gap-2 font-semibold text-secondary">
          <Info className="size-4 text-[var(--ci-teal-700)] shrink-0" />
          <span>Case Scoping & Advisory Model Boundary</span>
        </div>
        <p>
          Clinical intelligence structures and advisory drafts operate within a specific Case scope. You can test form validation in this global hub, or enter a target Case UUID above to navigate to the case-bound intelligence workspace. All drafts are strictly advisory decision-support artifacts.
        </p>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview & Structuring</TabsTrigger>
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
                Dispatch Structuring Evaluation
              </h2>
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
