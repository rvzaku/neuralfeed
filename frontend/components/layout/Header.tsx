"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/",         label: "Feed" },
  { href: "/discover", label: "Discover" },
  { href: "/topics",   label: "Topics" },
  { href: "/sources",  label: "Sources" },
  { href: "/settings", label: "Settings" },
];
import { ThemeToggle } from "./ThemeToggle";
import { RefreshIndicator } from "@/components/feed/RefreshIndicator";
import { SearchModal } from "@/components/feed/SearchModal";

export function Header() {
  const [searchOpen, setSearchOpen] = useState(false);
  const pathname = usePathname();

  return (
    <>
      <header className="hidden md:flex items-center justify-between px-6 py-3 border-b border-border bg-background/80 backdrop-blur-sm sticky top-[var(--banner-h,0px)] z-20">
        <div className="flex items-center gap-2">
          <span className="font-serif font-bold text-lg tracking-tight text-foreground">
            NeuralFeed
          </span>
          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary">
            beta
          </span>
        </div>

        {/* Desktop nav — mirrors the mobile dock */}
        <nav className="flex items-center gap-1" aria-label="Primary">
          {NAV_LINKS.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "px-3.5 py-1.5 rounded-full text-sm font-semibold transition-all",
                  active
                    ? "bg-foreground text-background shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                {label}
              </Link>
            );
          })}
        </nav>

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
