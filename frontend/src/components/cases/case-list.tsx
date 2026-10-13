"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Plus, ArrowRight, AlertCircle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function CaseList() {
  const router = useRouter();
  const [lookupId, setLookupId] = React.useState("");
  const [lookupError, setLookupError] = React.useState("");

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = lookupId.trim();
    if (!trimmed) {
      setLookupError("Please enter a Case UUID.");
      return;
    }
    if (!UUID_REGEX.test(trimmed)) {
      setLookupError("Case ID must be a valid RFC 4122 UUID.");
      return;
    }
    setLookupError("");
    router.push(`/cases/${trimmed}`);
  };

  return (
    <div className="space-y-6">
      {/* Blocker Notice */}
      <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-semibold">
          <Info className="size-4 text-amber-700 shrink-0" />
          <span>Case Browsing & Search Unavailable (BG-002)</span>
        </div>
        <p>
          The backend provides <code className="bg-amber-100 px-1 py-0.5 rounded">GET /api/v1/cases/{`{id}`}</code> for direct retrieval by identifier, but does not provide a general list or search endpoint (<code className="bg-amber-100 px-1 py-0.5 rounded">GET /api/v1/cases</code>). Use exact Case UUID lookup below to view an existing case record.
        </p>
      </div>

      {/* Action & Lookup Bar */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
        {/* Exact UUID Lookup */}
        <form onSubmit={handleLookup} className="flex flex-col sm:flex-row items-start sm:items-center gap-2 w-full md:w-auto">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="Exact Case UUID (e.g. 550e8400...)"
              value={lookupId}
              onChange={(e) => {
                setLookupId(e.target.value);
                if (lookupError) setLookupError("");
              }}
              className="pl-9 font-serif text-xs"
              aria-label="Exact Case UUID lookup"
            />
          </div>
          <Button type="submit" variant="secondary" size="sm" className="whitespace-nowrap">
            Open Case
            <ArrowRight className="ml-1.5 size-3.5" />
          </Button>
        </form>

        <Button render={<Link href="/cases/new" />} className="w-full md:w-auto">
          <Plus className="mr-2 size-4" />
          Create Case
        </Button>
      </div>

      {lookupError && (
        <p className="text-xs text-[var(--status-error-text)] font-serif flex items-center gap-1 -mt-3">
          <AlertCircle className="size-3" /> {lookupError}
        </p>
      )}

      {/* Contract-Aligned Data Table */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead className="font-serif font-semibold text-secondary w-[220px]">Case ID</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[220px]">Synthetic Subject ID</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[130px]">State</TableHead>
              <TableHead className="font-serif font-semibold text-secondary w-[90px]">Version</TableHead>
              <TableHead className="font-serif font-semibold text-secondary text-right">Created At</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell colSpan={5} className="h-64">
                <EmptyState
                  icon={<Search className="size-8 text-muted-foreground" />}
                  title="No Cases Loaded"
                  description="Backend case listing endpoint is not implemented (BG-002). Open an individual case by entering its exact UUID above or initialize a new case."
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>

      {/* Pagination Status */}
      <div className="flex items-center justify-between text-xs font-serif text-muted-foreground">
        <span>Displaying exact lookups only • Case list queries pending backend support (BG-002)</span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" disabled>Previous</Button>
          <Button variant="outline" size="sm" disabled>Next</Button>
        </div>
      </div>
    </div>
  );
}
