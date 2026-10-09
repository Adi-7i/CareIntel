import * as React from "react";
import { EmptyState } from "@/components/ui/empty-state";
import { Clock } from "lucide-react";

interface PlaceholderPageProps {
  title: string;
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <div className="space-y-6 max-w-5xl h-full flex flex-col">
      <header>
        <h1 className="font-serif text-3xl font-semibold text-secondary tracking-tight">{title}</h1>
        <p className="text-muted-foreground mt-1 text-sm">Navigation destination reserved for future implementation.</p>
      </header>

      <div className="flex-1 flex flex-col justify-center py-12">
        <EmptyState
          icon={<Clock className="size-8" />}
          title={`${title} (Coming Soon)`}
          description="This section will be available in a future phase. No mock data or fabricated clinical content is presented here."
          className="max-w-2xl mx-auto w-full bg-surface"
        />
      </div>
    </div>
  );
}
