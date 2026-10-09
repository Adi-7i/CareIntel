"use client";

import * as React from "react";
import { Search, RefreshCw, ClipboardList } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import { ReviewQueueBadge } from "@/components/review/review-queue-badge";

export function ReviewQueueList() {
  const [statusFilter, setStatusFilter] = React.useState<string>("all");
  const [assignedTo, setAssignedTo] = React.useState<string>("");

  return (
    <div className="space-y-6">
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <ClipboardList className="size-4" />
            Review Queue
          </h2>
          
          <div className="flex items-center gap-3">
            <Select value={statusFilter} onValueChange={(val) => setStatusFilter(val || "all")}>
              <SelectTrigger className="w-[180px] h-9">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="PENDING_ASSIGNMENT">Pending Assignment</SelectItem>
                <SelectItem value="ASSIGNED">Assigned</SelectItem>
                <SelectItem value="IN_REVIEW">In Review</SelectItem>
                <SelectItem value="CLARIFICATION_PENDING">Clarification Pending</SelectItem>
                <SelectItem value="REVIEW_COMPLETE">Review Complete</SelectItem>
                <SelectItem value="ESCALATED">Escalated</SelectItem>
              </SelectContent>
            </Select>
            
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
              <Input 
                placeholder="Assigned to (UUID)..." 
                value={assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
                className="pl-9 h-9 w-[220px]"
              />
            </div>
            
            <Button variant="outline" size="icon" className="h-9 w-9 shrink-0">
              <RefreshCw className="size-4" />
              <span className="sr-only">Refresh Queue</span>
            </Button>
          </div>
        </div>
        
        <div className="p-6">
          <EmptyState
            icon={<ClipboardList className="size-8" />}
            title="Queue Disconnected"
            description="The queue is ready but requires backend integration to display active review items. Adjusting filters will trigger backend queries once integrated."
          />
        </div>
      </div>
    </div>
  );
}
