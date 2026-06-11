"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

interface SavedView {
  label: string;
  emoji: string;
  params: Record<string, string>;
}

const SAVED_VIEWS: SavedView[] = [
  {
    label: "Default",
    emoji: "🏠",
    params: { time_range: "7d" },
  },
  {
    label: "Morning Digest",
    emoji: "☀️",
    params: { time_range: "1d", is_read: "false" },
  },
  {
    label: "Papers Only",
    emoji: "📄",
    params: { category: "research", time_range: "7d" },
  },
  {
    label: "Trending",
    emoji: "🔥",
    params: { ranked: "true", time_range: "3d" },
  },
  {
    label: "Open Source",
    emoji: "⚙️",
    params: { category: "github", time_range: "7d" },
  },
  {
    label: "Company Blogs",
    emoji: "🏢",
    params: { category: "company", time_range: "7d" },
  },
  {
    label: "Newsletters",
    emoji: "📬",
    params: { category: "newsletter", time_range: "7d" },
  },
];

function viewMatches(view: SavedView, params: URLSearchParams): boolean {
  for (const [k, v] of Object.entries(view.params)) {
    if (params.get(k) !== v) return false;
  }
  // Extra params (beyond what the view defines) means it's not a clean match
  const definedKeys = new Set(Object.keys(view.params));
  const filterKeys = ["category", "time_range", "is_read", "ranked", "topic", "source_id"];
  for (const k of filterKeys) {
    if (!definedKeys.has(k) && params.has(k)) return false;
  }
  return true;
}

export function SavedViewSwitcher() {
  const router = useRouter();
  const params = useSearchParams();

  function activate(view: SavedView) {
    const next = new URLSearchParams();
    for (const [k, v] of Object.entries(view.params)) {
      next.set(k, v);
    }
    router.push(`?${next.toString()}`, { scroll: false });
  }

  return (
    <div className="flex gap-2 overflow-x-auto scrollbar-none px-4 py-3">
      {SAVED_VIEWS.map((view) => {
        const active = viewMatches(view, params);
        return (
          <button
            key={view.label}
            onClick={() => activate(view)}
            className={cn(
              "shrink-0 flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-all whitespace-nowrap border",
              active
                ? "bg-primary text-primary-foreground border-primary shadow-sm"
                : "bg-muted/40 text-muted-foreground border-border hover:bg-muted hover:text-foreground"
            )}
          >
            <span>{view.emoji}</span>
            {view.label}
          </button>
        );
      })}
    </div>
  );
}
