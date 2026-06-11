"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { FilterContent } from "./FilterContent";

interface SavedView {
  label: string;
  emoji: string;
  params: Record<string, string>;
}

const SAVED_VIEWS: SavedView[] = [
  { label: "Default",        emoji: "🏠", params: { time_range: "7d" } },
  { label: "Morning Digest", emoji: "☀️", params: { time_range: "1d", is_read: "false" } },
  { label: "Papers Only",    emoji: "📄", params: { category: "research", time_range: "7d" } },
  { label: "Trending",       emoji: "🔥", params: { ranked: "true", time_range: "3d" } },
  { label: "Open Source",    emoji: "⚙️", params: { category: "github", time_range: "7d" } },
  { label: "Company Blogs",  emoji: "🏢", params: { category: "company", time_range: "7d" } },
  { label: "Newsletters",    emoji: "📬", params: { category: "newsletter", time_range: "7d" } },
  { label: "Podcasts",       emoji: "🎙️", params: { category: "podcast", time_range: "7d" } },
];

const FILTER_KEYS = ["category", "time_range", "is_read", "ranked", "topic", "source_id"];

function viewMatches(view: SavedView, params: URLSearchParams): boolean {
  for (const [k, v] of Object.entries(view.params)) {
    if (params.get(k) !== v) return false;
  }
  const defined = new Set(Object.keys(view.params));
  for (const k of FILTER_KEYS) {
    if (!defined.has(k) && params.has(k)) return false;
  }
  return true;
}

export function DesktopSidebar() {
  const router = useRouter();
  const params = useSearchParams();

  function activate(view: SavedView) {
    const next = new URLSearchParams();
    for (const [k, v] of Object.entries(view.params)) next.set(k, v);
    router.push(`?${next.toString()}`, { scroll: false });
  }

  return (
    <aside className="hidden lg:flex flex-col w-64 xl:w-72 shrink-0 border-r border-border sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto">
      <div className="px-4 py-5 space-y-6">
        {/* Saved views — vertical list */}
        <section>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Views
          </p>
          <div className="space-y-1">
            {SAVED_VIEWS.map((view) => {
              const active = viewMatches(view, params);
              return (
                <button
                  key={view.label}
                  onClick={() => activate(view)}
                  className={cn(
                    "w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors text-left",
                    active
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <span className="text-base leading-none">{view.emoji}</span>
                  {view.label}
                </button>
              );
            })}
          </div>
        </section>

        <div className="border-t border-border" />

        {/* Filter sections */}
        <FilterContent />
      </div>
    </aside>
  );
}
