"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { RefreshIndicator } from "@/components/feed/RefreshIndicator";
import { SearchModal } from "@/components/feed/SearchModal";

export function Header() {
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <>
      <header className="hidden md:flex items-center justify-between px-6 py-3 border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-20">
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg tracking-tight">NeuralFeed</span>
          <span className="text-xs text-muted-foreground font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary">
            beta
          </span>
        </div>

        <button
          onClick={() => setSearchOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-muted/50 hover:bg-muted transition-colors text-sm text-muted-foreground w-48"
        >
          <Search className="h-3.5 w-3.5" />
          <span className="flex-1 text-left">Search…</span>
          <kbd className="hidden xl:inline text-[10px] px-1 py-0.5 rounded bg-background border border-border font-mono">
            ⌘K
          </kbd>
        </button>

        <div className="flex items-center gap-1">
          <RefreshIndicator />
          <ThemeToggle />
        </div>
      </header>

      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
