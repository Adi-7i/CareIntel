"use client";

import * as React from "react";
import { Activity, Clock, Info, CheckCircle2, XCircle, Timer, Ban } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { TaskStatus, AsyncTaskResponse } from "@/types";

interface TaskStatusPanelProps {
  tasks?: AsyncTaskResponse[];
}

export function TaskStatusBadge({ status }: { status: TaskStatus }) {
  let colorClass = "";
  let icon = null;

  switch (status) {
    case "PENDING":
      colorClass = "bg-slate-100 text-slate-700 border-slate-300";
      icon = <Clock className="mr-1 size-3" />;
      break;
    case "QUEUED":
      colorClass = "bg-[var(--status-info-surface)] text-[var(--status-info-text)] border-[var(--status-info)]";
      icon = <Timer className="mr-1 size-3" />;
      break;
    case "RUNNING":
      colorClass = "bg-sky-50 text-sky-800 border-sky-300";
      icon = <Activity className="mr-1 size-3 animate-spin" />;
      break;
    case "SUCCEEDED":
      colorClass = "bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]";
      icon = <CheckCircle2 className="mr-1 size-3" />;
      break;
    case "FAILED":
      colorClass = "bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]";
      icon = <XCircle className="mr-1 size-3" />;
      break;
    case "CANCELLED":
      colorClass = "bg-muted text-muted-foreground border-slate-300";
      icon = <Ban className="mr-1 size-3" />;
      break;
  }

  return (
    <Badge
      variant="outline"
      className={`font-serif text-[11px] font-semibold uppercase tracking-wider rounded-md inline-flex items-center ${colorClass}`}
    >
      {icon}
      {status}
    </Badge>
  );
}

export function TaskStatusPanel({ tasks = [] }: TaskStatusPanelProps) {
  return (
    <div className="space-y-6">
      {/* Blocker & Contract Notice */}
      <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-xs font-serif text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-semibold">
          <Info className="size-4 text-amber-700 shrink-0" />
          <span>Task Result Retrieval Gap (BG-006, requirement.md §6)</span>
        </div>
        <p>
          Asynchronous processor tasks return <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">AsyncTaskResponse</code> containing status markers. The underlying task result payload is omitted from the async envelope, and run ID extraction is unmapped. No simulated progress bars or fake percent completions are shown.
        </p>
      </div>

      {/* Task State Reference Guide */}
      <div className="border rounded-lg bg-surface p-4 shadow-sm space-y-2">
        <h4 className="font-serif font-semibold text-secondary text-xs uppercase tracking-wider">
          Task Status State Descriptions
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-[11px] font-serif">
          <div className="p-2 rounded border bg-slate-50/50">
            <span className="font-semibold text-slate-800">PENDING</span>
            <p className="text-muted-foreground mt-0.5">Created envelope, awaits scheduler.</p>
          </div>
          <div className="p-2 rounded border bg-slate-50/50">
            <span className="font-semibold text-slate-800">QUEUED</span>
            <p className="text-muted-foreground mt-0.5">Enqueued in worker job queue.</p>
          </div>
          <div className="p-2 rounded border bg-slate-50/50">
            <span className="font-semibold text-slate-800">RUNNING</span>
            <p className="text-muted-foreground mt-0.5">Active processor execution.</p>
          </div>
          <div className="p-2 rounded border bg-slate-50/50">
            <span className="font-semibold text-slate-800">SUCCEEDED</span>
            <p className="text-muted-foreground mt-0.5">Task concluded without fault.</p>
          </div>
          <div className="p-2 rounded border bg-slate-50/50">
            <span className="font-semibold text-slate-800">FAILED</span>
            <p className="text-muted-foreground mt-0.5">Execution aborted with error.</p>
          </div>
          <div className="p-2 rounded border bg-slate-50/50">
            <span className="font-semibold text-slate-800">CANCELLED</span>
            <p className="text-muted-foreground mt-0.5">Terminated prior to completion.</p>
          </div>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2 text-sm">
            <Activity className="size-4 text-[var(--ci-teal-700)]" />
            Asynchronous Task Register (AsyncTaskResponse)
          </h2>
          <span className="text-xs font-serif text-muted-foreground">
            {tasks.length} {tasks.length === 1 ? "task" : "tasks"}
          </span>
        </div>

        {tasks.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<Activity className="size-8 text-muted-foreground" />}
              title="No Asynchronous Tasks Queued"
              description="Dispatch a processing run above to enqueue asynchronous OCR, transcription, or extraction tasks."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30 text-xs">
                <TableHead className="font-serif font-semibold text-secondary w-[200px]">Task ID</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[160px]">Task Type</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[200px]">Entity ID</TableHead>
                <TableHead className="font-serif font-semibold text-secondary w-[130px]">Status</TableHead>
                <TableHead className="font-serif font-semibold text-secondary text-right w-[140px]">Created At</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tasks.map((task) => (
                <TableRow key={task.task_id} className="text-xs font-serif">
                  <TableCell className="font-mono text-secondary truncate">{task.task_id}</TableCell>
                  <TableCell className="font-mono">{task.task_type}</TableCell>
                  <TableCell className="font-mono truncate">{task.entity_id}</TableCell>
                  <TableCell>
                    <TaskStatusBadge status={task.status} />
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">{task.created_at}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
