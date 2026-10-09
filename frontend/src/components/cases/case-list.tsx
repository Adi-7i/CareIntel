"use client";

import * as React from "react";
import Link from "next/link";
import { Search, Plus, Filter, ArrowUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function CaseList() {
  const [search, setSearch] = React.useState("");

  return (
    <div className="space-y-6">
      {/* Action Bar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="flex w-full sm:w-auto items-center gap-2">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="Search cases..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button variant="outline" size="icon" aria-label="Filter cases">
            <Filter className="size-4" />
          </Button>
        </div>
        
        <Button render={<Link href="/cases/new" />} className="w-full sm:w-auto">
          <Plus className="mr-2 size-4" />
          Create Case
        </Button>
      </div>

      {/* Data Table */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead className="w-[120px] font-serif font-semibold text-secondary">
                <Button variant="ghost" className="h-8 p-0 hover:bg-transparent font-semibold">
                  Case ID
                  <ArrowUpDown className="ml-2 size-3" />
                </Button>
              </TableHead>
              <TableHead className="font-serif font-semibold text-secondary">Title</TableHead>
              <TableHead className="font-serif font-semibold text-secondary">Patient Identifier</TableHead>
              <TableHead className="font-serif font-semibold text-secondary">Priority</TableHead>
              <TableHead className="font-serif font-semibold text-secondary text-right">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell colSpan={5} className="h-64">
                <EmptyState
                  icon={<Search className="size-8" />}
                  title="No cases found"
                  description="Cases will appear here when connected to the backend. No mock data is presented."
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>

      {/* Pagination Placeholder */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>Showing 0 of 0 cases</span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" disabled>Previous</Button>
          <Button variant="outline" size="sm" disabled>Next</Button>
        </div>
      </div>
    </div>
  );
}
