"use client";

import * as React from "react";
import { Menu, Search, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Breadcrumb } from "@/components/navigation/breadcrumb";

interface AppHeaderProps {
  onOpenMobileNav: () => void;
}

export function AppHeader({ onOpenMobileNav }: AppHeaderProps) {
  return (
    <header role="banner" className="flex items-center justify-between h-16 px-4 md:px-6 border-b border-border bg-surface shrink-0">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onOpenMobileNav}
          aria-label="Open navigation"
        >
          <Menu className="size-5" />
        </Button>
        <Breadcrumb />
      </div>

      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger render={<Button variant="ghost" size="icon" aria-label="Search" />}>
            <Search className="size-5 text-muted-foreground" />
          </TooltipTrigger>
          <TooltipContent className="font-serif">
            Search will be available in a future phase.
          </TooltipContent>
        </Tooltip>

        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="rounded-full bg-muted/50 border border-border" aria-label="User menu" />}>
            <User className="size-5 text-muted-foreground" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 font-serif">
            <DropdownMenuItem disabled>
              <span className="font-medium text-foreground">Sign In / Account</span>
              <span className="ml-auto text-xs text-muted-foreground">(Soon)</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem disabled>
              Preferences
            </DropdownMenuItem>
            <DropdownMenuItem disabled>
              Log Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
