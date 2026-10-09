"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { cn } from "cn";
import { 
  LayoutDashboard, 
  FolderOpen, 
  FileText, 
  BrainCircuit, 
  ClipboardCheck, 
  ArrowUpFromLine,
  PanelLeftClose,
  PanelLeftOpen
} from "lucide-react";
import { NavItemType } from "@/types/navigation";
import { NavItem } from "@/components/navigation/nav-item";
import { Button } from "@/components/ui/button";

const navItems: NavItemType[] = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/cases", label: "Cases", icon: FolderOpen },
  { href: "/evidence", label: "Evidence", icon: FileText },
  { href: "/intelligence", label: "Clinical Intelligence", icon: BrainCircuit },
  { href: "/review", label: "Review Workspace", icon: ClipboardCheck },
  { href: "/escalations", label: "Escalations & Handoffs", icon: ArrowUpFromLine },
];

interface AppSidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  className?: string;
}

export function AppSidebar({ isCollapsed, onToggleCollapse, className }: AppSidebarProps) {
  const pathname = usePathname();

  const isRouteActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  return (
    <aside
      role="complementary"
      aria-label="Main navigation"
      className={cn(
        "flex flex-col h-full bg-secondary text-secondary-foreground border-r border-border/20 transition-[width] duration-200 ease-in-out shrink-0",
        isCollapsed ? "w-16" : "w-64",
        className
      )}
    >
      <div className={cn("flex items-center h-16 shrink-0", isCollapsed ? "justify-center px-0" : "px-6")}>
        {!isCollapsed ? (
          <span className="font-serif text-xl font-semibold tracking-tight text-white">CareIntel</span>
        ) : (
          <span className="font-serif text-xl font-bold text-primary">C</span>
        )}
      </div>

      <nav role="navigation" aria-label="Primary navigation" className="flex-1 overflow-y-auto overflow-x-hidden py-4 px-3 space-y-1">
        {navItems.map((item) => (
          <NavItem
            key={item.href}
            {...item}
            isActive={isRouteActive(item.href)}
            isCollapsed={isCollapsed}
          />
        ))}
      </nav>

      <div className="p-3 shrink-0">
        <Button
          variant="ghost"
          size={isCollapsed ? "icon" : "default"}
          onClick={onToggleCollapse}
          className={cn(
            "w-full text-secondary-foreground hover:bg-white/5 hover:text-white justify-start",
            isCollapsed && "justify-center"
          )}
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <PanelLeftOpen className="size-5" /> : (
            <>
              <PanelLeftClose className="size-5 mr-3 shrink-0" />
              <span className="font-serif">Collapse</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}
