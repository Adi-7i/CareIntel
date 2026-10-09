"use client";

import * as React from "react";
import { Search, AlertCircle, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "cn";

export function RetrievalForm() {
  const [caseId, setCaseId] = React.useState("");
  const [query, setQuery] = React.useState("");
  const [corpusVersion, setCorpusVersion] = React.useState("");
  const [searchMode, setSearchMode] = React.useState("");
  const [topK, setTopK] = React.useState("10");
  
  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!caseId.trim()) newErrors.caseId = "Case ID is required.";
    if (!query.trim()) newErrors.query = "Search query is required.";
    if (!corpusVersion.trim()) newErrors.corpusVersion = "Corpus version is required.";
    if (!searchMode) newErrors.searchMode = "Search mode must be selected.";
    const topKNum = parseInt(topK, 10);
    if (isNaN(topKNum) || topKNum < 1 || topKNum > 50) newErrors.topK = "Top K must be between 1 and 50.";
    return newErrors;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (status === "submitting") return;

    const newErrors = validate();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setStatus("submitting");

    setTimeout(() => {
      setStatus("unconnected");
    }, 800);
  };

  return (
    <div className="space-y-8">
      {status === "unconnected" && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4">
          <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold mb-1">
            Authentication Disconnected
          </p>
          <p className="font-serif text-sm text-[var(--status-info-text)]">
            Query validated locally. Actual trusted-knowledge retrieval requires integration.
          </p>
        </div>
      )}

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <Search className="size-4" />
            Knowledge Retrieval
          </h2>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6" aria-label="Retrieval form">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="retCaseId" className={errors.caseId ? "text-destructive" : ""}>Target Case ID *</Label>
                <Input
                  id="retCaseId"
                  value={caseId}
                  onChange={(e) => {
                    setCaseId(e.target.value);
                    if (errors.caseId) setErrors({ ...errors, caseId: "" });
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.caseId}
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                />
                {errors.caseId && (
                  <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.caseId}
                  </p>
                )}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="corpusVersion" className={errors.corpusVersion ? "text-destructive" : ""}>Corpus Version *</Label>
                <Input
                  id="corpusVersion"
                  value={corpusVersion}
                  onChange={(e) => {
                    setCorpusVersion(e.target.value);
                    if (errors.corpusVersion) setErrors({ ...errors, corpusVersion: "" });
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.corpusVersion}
                  placeholder="e.g. guidelines-2026-v2"
                />
                {errors.corpusVersion && (
                  <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.corpusVersion}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="query" className={errors.query ? "text-destructive" : ""}>Search Query *</Label>
              <Input
                id="query"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  if (errors.query) setErrors({ ...errors, query: "" });
                }}
                disabled={status === "submitting"}
                aria-invalid={!!errors.query}
                placeholder="Enter clinical retrieval query..."
              />
              {errors.query && (
                <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" /> {errors.query}
                </p>
              )}
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="searchMode" className={errors.searchMode ? "text-destructive" : ""}>Search Mode *</Label>
                <Select
                  value={searchMode}
                  onValueChange={(val) => {
                    setSearchMode(val || "");
                    if (errors.searchMode) setErrors({ ...errors, searchMode: "" });
                  }}
                  disabled={status === "submitting"}
                >
                  <SelectTrigger id="searchMode" className={cn(errors.searchMode && "border-destructive focus-visible:ring-destructive/50")}>
                    <SelectValue placeholder="Select mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="HYBRID">Hybrid (Dense + Sparse)</SelectItem>
                    <SelectItem value="DENSE">Dense (Semantic)</SelectItem>
                    <SelectItem value="SPARSE">Sparse (Keyword)</SelectItem>
                  </SelectContent>
                </Select>
                {errors.searchMode && (
                  <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.searchMode}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="topK" className={errors.topK ? "text-destructive" : ""}>Top K Results *</Label>
                <Input
                  id="topK"
                  type="number"
                  min="1"
                  max="50"
                  value={topK}
                  onChange={(e) => {
                    setTopK(e.target.value);
                    if (errors.topK) setErrors({ ...errors, topK: "" });
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.topK}
                />
                {errors.topK && (
                  <p className="text-sm text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.topK}
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={status === "submitting"} aria-busy={status === "submitting"}>
                {status === "submitting" ? "Searching..." : (
                  <>
                    <Search className="mr-2 size-4" />
                    Retrieve Knowledge
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <Database className="size-4" />
            Retrieval Candidates
          </h2>
        </div>
        <div className="p-6">
          <EmptyState
            icon={<Database className="size-8" />}
            title="No Candidates Found"
            description="Run a retrieval query to view ranked source identifiers."
          />
        </div>
      </div>
    </div>
  );
}
