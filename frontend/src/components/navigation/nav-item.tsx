"use client";

import * as React from "react";
import Link from "next/link";
import { cn } from "cn";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { NavItemType } from "@/types/navigation";

interface NavItemProps extends NavItemType {
  isActive: boolean;
  isCollapsed: boolean;
}

export function NavItem({ href, label, icon: Icon, isActive, isCollapsed }: NavItemProps) {
  const linkContent = (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-serif transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-[var(--secondary)]",
        isActive
          ? "bg-primary/10 text-primary border-l-2 border-primary rounded-l-none pl-[10px]"
          : "text-secondary-foreground hover:bg-white/5 hover:text-white",
        isCollapsed && "justify-center px-0 border-l-0 rounded-md"
      )}
      aria-current={isActive ? "page" : undefined}
    >
      <Icon className="size-5 shrink-0" />
      {!isCollapsed && <span>{label}</span>}
    </Link>
  );

  if (isCollapsed) {
    return (
      <Tooltip>
        <TooltipTrigger render={linkContent} />
        <TooltipContent side="right" sideOffset={16} className="font-serif">
          {label}
        </TooltipContent>
      </Tooltip>
    );
  }

  return linkContent;
}
