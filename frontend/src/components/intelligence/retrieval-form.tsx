"use client";

import * as React from "react";
import { Search, AlertCircle, Database, Info, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState } from "@/components/ui/empty-state";
import type { RetrievalRequest, SearchMode } from "@/types";
import { cn } from "cn";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const STRICT_INTEGER_REGEX = /^\d+$/;

interface RetrievalFormProps {
  caseId?: string;
}

export function RetrievalForm({ caseId: initialCaseId = "" }: RetrievalFormProps) {
  const [caseId, setCaseId] = React.useState(initialCaseId);
  const [query, setQuery] = React.useState("");
  const [corpusVersion, setCorpusVersion] = React.useState("1");
  const [searchMode, setSearchMode] = React.useState<SearchMode>("hybrid");
  const [topK, setTopK] = React.useState("10");

  const [status, setStatus] = React.useState<"idle" | "submitting" | "unconnected">("idle");
  const [validatedPayload, setValidatedPayload] = React.useState<RetrievalRequest | null>(null);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!caseId.trim()) {
      newErrors.caseId = "Target Case ID is required.";
    } else if (!UUID_REGEX.test(caseId.trim())) {
      newErrors.caseId = "Case ID must be a valid RFC 4122 UUID.";
    }

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      newErrors.query = "Search query is required.";
    } else if (trimmedQuery.length > 4000) {
      newErrors.query = "Search query must not exceed 4,000 characters.";
    }

    // Strict integer validation (reject decimals like "1.5" and non-numeric strings)
    const trimmedCorpus = corpusVersion.trim();
    if (!trimmedCorpus || !STRICT_INTEGER_REGEX.test(trimmedCorpus)) {
      newErrors.corpusVersion = "Corpus version must be an integer between 1 and 100 (no decimals).";
    } else {
      const cvNum = Number(trimmedCorpus);
      if (cvNum < 1 || cvNum > 100) {
        newErrors.corpusVersion = "Corpus version must be an integer between 1 and 100.";
      }
    }

    if (!searchMode) {
      newErrors.searchMode = "Search mode must be selected.";
    }

    const trimmedTopK = topK.trim();
    if (!trimmedTopK || !STRICT_INTEGER_REGEX.test(trimmedTopK)) {
      newErrors.topK = "Top K must be an integer between 1 and 50 (no decimals).";
    } else {
      const topKNum = Number(trimmedTopK);
      if (topKNum < 1 || topKNum > 50) {
        newErrors.topK = "Top K must be between 1 and 50.";
      }
    }

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

    const payload: RetrievalRequest = {
      query: query.trim(),
      corpus_version: Number(corpusVersion.trim()),
      top_k: Number(topK.trim()),
      search_mode: searchMode,
    };

    setValidatedPayload(payload);

    setTimeout(() => {
      setStatus("unconnected");
    }, 400);
  };

  return (
    <div className="space-y-8">
      {/* Blocker & Semantic Calibration Notice */}
      <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-semibold">
          <Info className="size-4 text-amber-700 shrink-0" />
          <span>Knowledge Base Passages & Scoring Notice (BG-019, requirement.md §6)</span>
        </div>
        <p>
          Retrieval ranks trusted clinical guideline documents. Document chunking, snippet extraction, and verbatim source passages are currently omitted from backend responses (BG-019). Furthermore, <span className="font-semibold">retrieval scores denote vector/lexical search relevance, not clinical accuracy or diagnostic confidence</span>.
        </p>
      </div>

      {status === "unconnected" && validatedPayload && (
        <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 space-y-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-[var(--status-info-text)] shrink-0" />
            <p className="font-serif text-xs text-[var(--status-info-text)] font-semibold">
              Retrieval Query Validated Locally (RetrievalRequest)
            </p>
          </div>
          <p className="font-serif text-xs text-[var(--status-info-text)]">
            Retrieval parameters conform to schema. Live search requires POST <code className="bg-white/60 px-1 py-0.5 rounded">/api/v1/cases/{caseId}/retrieval</code>.
          </p>
          <div className="bg-white/80 p-2.5 rounded text-xs font-mono border overflow-x-auto text-slate-800">
            {JSON.stringify(validatedPayload, null, 2)}
          </div>
        </div>
      )}

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <Search className="size-4 text-[var(--ci-teal-700)]" />
            Clinical Knowledge Retrieval Query (FE-016)
          </h2>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6" aria-label="Retrieval form">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="retCaseId" className={errors.caseId ? "text-destructive" : ""}>
                  Target Case ID *
                </Label>
                <Input
                  id="retCaseId"
                  value={caseId}
                  onChange={(e) => {
                    setCaseId(e.target.value);
                    if (errors.caseId) setErrors((prev) => ({ ...prev, caseId: "" }));
                  }}
                  disabled={status === "submitting" || Boolean(initialCaseId)}
                  aria-invalid={!!errors.caseId}
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                  className={errors.caseId ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
                />
                {errors.caseId && (
                  <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.caseId}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="corpusVersion" className={errors.corpusVersion ? "text-destructive" : ""}>
                  Corpus Version (Strict Integer 1–100) *
                </Label>
                <Input
                  id="corpusVersion"
                  value={corpusVersion}
                  onChange={(e) => {
                    setCorpusVersion(e.target.value);
                    if (errors.corpusVersion) setErrors((prev) => ({ ...prev, corpusVersion: "" }));
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.corpusVersion}
                  placeholder="Integer 1 to 100"
                  className={errors.corpusVersion ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
                />
                {errors.corpusVersion && (
                  <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.corpusVersion}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label htmlFor="query" className={errors.query ? "text-destructive" : ""}>
                  Search Query *
                </Label>
                <span className="text-[11px] text-muted-foreground font-mono">
                  {query.length} / 4000 chars
                </span>
              </div>
              <Input
                id="query"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  if (errors.query) setErrors((prev) => ({ ...prev, query: "" }));
                }}
                disabled={status === "submitting"}
                aria-invalid={!!errors.query}
                placeholder="e.g. Pediatric prolonged febrile illness differential guidelines..."
                maxLength={4000}
                className={errors.query ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
              />
              {errors.query && (
                <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                  <AlertCircle className="size-3" /> {errors.query}
                </p>
              )}
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="searchMode" className={errors.searchMode ? "text-destructive" : ""}>
                  Search Mode *
                </Label>
                <Select
                  value={searchMode}
                  onValueChange={(val) => {
                    setSearchMode(val as SearchMode);
                    if (errors.searchMode) setErrors((prev) => ({ ...prev, searchMode: "" }));
                  }}
                  disabled={status === "submitting"}
                >
                  <SelectTrigger id="searchMode" className={cn("font-serif text-xs", errors.searchMode && "border-destructive focus-visible:ring-destructive/50")}>
                    <SelectValue placeholder="Select mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hybrid">hybrid (Vector Dense + BM25 Sparse)</SelectItem>
                    <SelectItem value="vector">vector (Dense Semantic Embeddings)</SelectItem>
                    <SelectItem value="keyword">keyword (Sparse Lexical BM25)</SelectItem>
                  </SelectContent>
                </Select>
                {errors.searchMode && (
                  <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.searchMode}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="topK" className={errors.topK ? "text-destructive" : ""}>
                  Top K Results (Integer 1–50) *
                </Label>
                <Input
                  id="topK"
                  value={topK}
                  onChange={(e) => {
                    setTopK(e.target.value);
                    if (errors.topK) setErrors((prev) => ({ ...prev, topK: "" }));
                  }}
                  disabled={status === "submitting"}
                  aria-invalid={!!errors.topK}
                  placeholder="Default: 10"
                  className={errors.topK ? "border-destructive font-serif text-xs" : "font-serif text-xs"}
                />
                {errors.topK && (
                  <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 mt-1">
                    <AlertCircle className="size-3" /> {errors.topK}
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" size="sm" disabled={status === "submitting"} aria-busy={status === "submitting"}>
                {status === "submitting" ? (
                  "Validating..."
                ) : (
                  <>
                    <Search className="mr-1.5 size-3.5" />
                    Query Trusted Knowledge
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>

      {/* Results Candidates Block */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <Database className="size-4 text-[var(--ci-teal-700)]" />
            Ranked Document Candidates (RetrievalResponse)
          </h2>
        </div>
        <div className="p-6">
          <EmptyState
            icon={<Database className="size-8 text-muted-foreground" />}
            title="No Retrieval Candidates Loaded"
            description="Execute a clinical search above to review top-ranked reference document identifiers and relevance metrics."
          />
        </div>
      </div>
    </div>
  );
}
