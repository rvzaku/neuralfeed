"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  Search, Rss, Compass, Tag, Settings, RefreshCw, Sun, Moon, Monitor,
  CalendarDays, CalendarRange, CalendarClock, CornerDownLeft,
} from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSearch: () => void;
  onRefresh: () => void;
  onHorizon: (h: "day" | "month" | "year") => void;
}

interface Command {
  id: string;
  label: string;
  group: string;
  icon: React.ComponentType<{ className?: string }>;
  keywords?: string;
  run: () => void;
}

export function CommandPalette({ isOpen, onClose, onSearch, onRefresh, onHorizon }: CommandPaletteProps) {
  const router = useRouter();
  const { setTheme } = useTheme();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: Command[] = useMemo(() => {
    const go = (path: string) => () => { onClose(); router.push(path); };
    return [
      { id: "search", label: "Search articles", group: "Actions", icon: Search, keywords: "find query", run: () => { onClose(); onSearch(); } },
      { id: "refresh", label: "Refresh feed", group: "Actions", icon: RefreshCw, keywords: "reload fetch", run: () => { onClose(); onRefresh(); } },
      { id: "nav-feed", label: "Go to Feed", group: "Navigate", icon: Rss, keywords: "home today", run: go("/") },
      { id: "nav-discover", label: "Go to Discover", group: "Navigate", icon: Compass, keywords: "explore search", run: go("/discover") },
      { id: "nav-topics", label: "Go to Topics", group: "Navigate", icon: Tag, keywords: "categories tags", run: go("/topics") },
      { id: "nav-sources", label: "Go to Sources", group: "Navigate", icon: Rss, keywords: "feeds providers", run: go("/sources") },
      { id: "nav-settings", label: "Go to Settings", group: "Navigate", icon: Settings, keywords: "preferences config", run: go("/settings") },
      { id: "h-day", label: "Horizon: Day", group: "Views", icon: CalendarDays, keywords: "today window", run: () => { onClose(); onHorizon("day"); } },
      { id: "h-month", label: "Horizon: Month", group: "Views", icon: CalendarRange, keywords: "window", run: () => { onClose(); onHorizon("month"); } },
      { id: "h-year", label: "Horizon: Year", group: "Views", icon: CalendarClock, keywords: "window annual", run: () => { onClose(); onHorizon("year"); } },
      { id: "theme-light", label: "Theme: Light", group: "Theme", icon: Sun, run: () => { onClose(); setTheme("light"); } },
      { id: "theme-dark", label: "Theme: Dark", group: "Theme", icon: Moon, run: () => { onClose(); setTheme("dark"); } },
      { id: "theme-system", label: "Theme: System", group: "Theme", icon: Monitor, run: () => { onClose(); setTheme("system"); } },
    ];
  }, [router, setTheme, onClose, onSearch, onRefresh, onHorizon]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter((c) =>
      (c.label + " " + c.group + " " + (c.keywords ?? "")).toLowerCase().includes(q)
    );
  }, [commands, query]);

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setActive(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => { setActive(0); }, [query]);

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") { e.preventDefault(); onClose(); return; }
      if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, filtered.length - 1)); }
      if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
      if (e.key === "Enter") { e.preventDefault(); filtered[active]?.run(); }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, filtered, active, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 px-4 pt-[12vh] backdrop-blur-sm fade-in"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-lg overflow-hidden rounded-xl border border-border bg-background shadow-2xl">
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command…"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            aria-label="Command"
          />
        </div>

        <ul className="max-h-[55vh] overflow-y-auto py-2" role="listbox">
          {filtered.length === 0 && (
            <li className="px-4 py-8 text-center text-sm text-muted-foreground">No commands found</li>
          )}
          {filtered.map((c, i) => {
            const Icon = c.icon;
            return (
              <li key={c.id} role="option" aria-selected={i === active}>
                <button
                  onMouseMove={() => setActive(i)}
                  onClick={c.run}
                  className={`flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                    i === active ? "bg-muted text-foreground" : "text-foreground/85 hover:bg-muted/60"
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="flex-1">{c.label}</span>
                  <span className="text-[10px] uppercase tracking-wider text-muted-foreground/60">{c.group}</span>
                  {i === active && <CornerDownLeft className="h-3.5 w-3.5 text-muted-foreground/60" />}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
