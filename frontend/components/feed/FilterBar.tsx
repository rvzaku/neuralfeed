"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Bookmark, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

const CONTENT_TYPES = [
  { label: "All",         value: "" },
  { label: "Papers",      value: "research" },
  { label: "GitHub",      value: "github" },
  { label: "Social",      value: "social" },
  { label: "Blogs",       value: "company" },
  { label: "Newsletters", value: "newsletter" },
  { label: "Videos",      value: "video" },
  { label: "Podcasts",    value: "podcast" },
  { label: "Funding",     value: "funding" },
];

const TIME_RANGES = [
  { label: "Today",  value: "1d" },
  { label: "3 days", value: "3d" },
  { label: "Week",   value: "7d" },
  { label: "Month",  value: "30d" },
];

interface FilterBarProps {
  onFilterClick?: () => void;
}

export function FilterBar({ onFilterClick }: FilterBarProps) {
  const router = useRouter();
  const params = useSearchParams();
  const activeCategory = params.get("category") ?? "";
  const activeTime     = params.get("time_range") ?? "7d";
  const savedOnly      = params.get("is_bookmarked") === "true";

  const hasAdvanced = params.has("topic") || params.has("source_id") || params.has("feedback") || params.has("min_signal");
  const hasActiveFilters = activeCategory !== "" || activeTime !== "7d" || hasAdvanced || savedOnly;

  function setParam(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    router.push(`?${next.toString()}`, { scroll: false });
  }

  return (
    <div className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border">
      <div className="px-4 pt-3 pb-2 space-y-2">
        {/* Content type pills + filter button (filter button hidden on desktop — sidebar handles it) */}
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5 overflow-x-auto scrollbar-none pb-0.5 flex-1">
            {CONTENT_TYPES.map((t) => (
              <button
                key={t.value}
                onClick={() => setParam("category", t.value)}
                className={cn(
                  "shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors whitespace-nowrap",
                  "min-h-[32px] border",
                  activeCategory === t.value
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-muted/50 text-muted-foreground border-border hover:bg-muted hover:text-foreground"
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Sliders button — only visible on mobile/tablet where there's no sidebar */}
          {onFilterClick && (
            <button
              onClick={onFilterClick}
              className={cn(
                "lg:hidden shrink-0 flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium border transition-colors min-h-[32px]",
                hasAdvanced
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-muted/50 text-muted-foreground border-border hover:bg-muted hover:text-foreground"
              )}
              aria-label="Advanced filters"
            >
              <SlidersHorizontal className="h-3 w-3" />
              {hasAdvanced && <span className="h-1.5 w-1.5 rounded-full bg-primary-foreground" />}
            </button>
          )}
        </div>

        {/* Time range + clear row */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex gap-1.5 overflow-x-auto scrollbar-none">
            <button
              onClick={() => setParam("is_bookmarked", savedOnly ? "" : "true")}
              className={cn(
                "shrink-0 flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition-colors whitespace-nowrap min-h-[32px] border",
                savedOnly
                  ? "bg-secondary text-secondary-foreground border-secondary"
                  : "bg-transparent text-muted-foreground border-transparent hover:border-border hover:text-foreground"
              )}
              aria-pressed={savedOnly}
            >
              <Bookmark className="h-3 w-3" />
              Saved
            </button>
            {TIME_RANGES.map((t) => (
              <button
                key={t.value}
                onClick={() => setParam("time_range", t.value)}
                className={cn(
                  "shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors whitespace-nowrap",
                  "min-h-[32px] border",
                  activeTime === t.value
                    ? "bg-secondary text-secondary-foreground border-secondary"
                    : "bg-transparent text-muted-foreground border-transparent hover:border-border hover:text-foreground"
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          {hasActiveFilters && (
            <button
              onClick={() => router.push("/", { scroll: false })}
              className="shrink-0 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
