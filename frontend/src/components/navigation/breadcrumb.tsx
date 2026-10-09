"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { cn } from "cn";

// Simple mapping for demo. In a real app, this might match against a defined route dictionary.
const segmentMap: Record<string, string> = {
  cases: "Cases",
  evidence: "Evidence",
  intelligence: "Clinical Intelligence",
  review: "Review Workspace",
  escalations: "Escalations & Handoffs",
  "design-system": "Design System",
};

export function Breadcrumb() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  return (
    <nav aria-label="Breadcrumb" className="hidden sm:flex">
      <ol className="flex items-center space-x-2 text-sm font-serif">
        <li>
          <Link 
            href="/" 
            className={cn(
              "transition-colors hover:text-foreground",
              segments.length === 0 ? "text-foreground font-medium" : "text-muted-foreground"
            )}
            aria-current={segments.length === 0 ? "page" : undefined}
          >
            Overview
          </Link>
        </li>
        {segments.map((segment, index) => {
          const isLast = index === segments.length - 1;
          const href = `/${segments.slice(0, index + 1).join("/")}`;
          const label = segmentMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);

          return (
            <React.Fragment key={href}>
              <li>
                <ChevronRight className="size-4 text-muted-foreground" />
              </li>
              <li>
                {isLast ? (
                  <span className="text-foreground font-medium" aria-current="page">
                    {label}
                  </span>
                ) : (
                  <Link href={href} className="text-muted-foreground transition-colors hover:text-foreground">
                    {label}
                  </Link>
                )}
              </li>
            </React.Fragment>
          );
        })}
      </ol>
    </nav>
  );
}
