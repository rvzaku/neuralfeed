"use client";

// V8 (app-feedback-v5): one For You page — ranked, capped, personalized
// card list. V6: smart ranking is always on and cannot be disabled. The two
// tabs differ only in freshness: "For You" hides items you've already opened;
// "All items" is the same ranking with viewed items kept, so you can browse
// back over what you've read. Filters live behind one button.

import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search, AlertCircle, Inbox, SlidersHorizontal } from "lucide-react";
import { FeedCard } from "./FeedCard";
import { FeedCardSkeleton } from "./FeedCardSkeleton";
import { FilterDrawer } from "./FilterDrawer";
import { RefreshIndicator } from "./RefreshIndicator";
import { SearchModal } from "./SearchModal";
import { SummarySheet } from "./SummarySheet";
import { useFeed } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";
import type { Article, FeedFilters } from "@/lib/types";

// time_range is driven by the Day/Month/Year horizon selector, not the filter
// drawer, so it is intentionally excluded from the filter count.
const FILTER_PARAMS = ["category", "topic", "source_id", "is_read", "is_bookmarked", "feedback"];

// V7 horizon catch-up: open the app a day / month / year later and see the most
// important + relevant items for that window (backend ranking is horizon-aware).
type Horizon = "day" | "month" | "year";
const HORIZON_RANGE: Record<Horizon, FeedFilters["time_range"]> = { day: "1d", month: "30d", year: "365d" };
const HORIZON_LABEL: [Horizon, string][] = [["day", "Day"], ["month", "Month"], ["year", "Year"]];
function rangeToHorizon(tr: string | null): Horizon {
  if (tr === "1d") return "day";
  if (tr === "365d") return "year";
  return "month";
}

export function FeedView() {
  const params = useSearchParams();
  const router = useRouter();
  const [searchOpen, setSearchOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [openArticle, setOpenArticle] = useState<Article | null>(null);

  // "For You" = ranked + personalized; "All" = raw chronological
  const view = params.get("view") === "all" ? "all" : "foryou";

  const filters: FeedFilters = useMemo(() => ({
    // category/topic/source_id may be comma-joined (multi-select); passed through
    // as CSV — the backend splits and builds IN / OR queries.
    category:    params.get("category") || undefined,
    topic:       params.get("topic") || undefined,
    source_id:   params.get("source_id") || undefined,
    time_range:  (params.get("time_range") as FeedFilters["time_range"]) || "30d",
    is_read:     params.get("is_read") === "false" ? false : params.get("is_read") === "true" ? true : undefined,
    is_bookmarked: params.get("is_bookmarked") === "true" ? true : undefined,
    feedback:    params.get("feedback") ? Number(params.get("feedback")) as FeedFilters["feedback"] : undefined,
    ranked:      true,            // V6: smart ranking is never disabled
    include_read: view === "all", // "All items" = ranked archive incl. viewed
    // V7-6: the Feed is a finite ranked shortlist — the backend caps it to the
    // feed-density setting (cap_to_density defaults true); 50 just holds the page.
    limit: 50,
  }), [params, view]);

  // Count every selected value (CSV members count individually) so the badge
  // reflects multi-select reality, not just how many dimensions are touched.
  const activeFilterCount = FILTER_PARAMS.reduce((n, k) => {
    const v = params.get(k);
    if (!v) return n;
    return n + (["category", "topic", "source_id"].includes(k) ? v.split(",").filter(Boolean).length : 1);
  }, 0);

  const { data, isLoading, isError, refetch } = useFeed(filters);
  const allItems = data?.items ?? [];
  // total == feed-density here: the backend caps the ranked Feed to the density
  // setting, so this is the finite "top N" count shown to the user.
  const total = data?.total ?? 0;

  const horizon = rangeToHorizon(params.get("time_range"));

  function setHorizon(h: Horizon) {
    const sp = new URLSearchParams(params.toString());
    sp.set("time_range", HORIZON_RANGE[h] as string);
    router.push(`?${sp.toString()}`, { scroll: false });
  }

  function setView(next: "foryou" | "all") {
    const sp = new URLSearchParams(params.toString());
    if (next === "all") sp.set("view", "all");
    else sp.delete("view");
    router.push(`?${sp.toString()}`, { scroll: false });
  }

  return (
    <div className="flex min-h-screen">
      <div className="flex flex-col flex-1 min-w-0">
        <main className="flex-1 px-4 pt-4 pb-24 md:pb-6 lg:pb-8 max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto w-full space-y-3">

          {/* Mobile mini-header (the desktop global Header owns brand/search/refresh,
              so this row is mobile-only to avoid duplicated chrome). */}
          <div className="flex items-center justify-between gap-2 md:hidden">
            <h1 className="font-serif font-semibold text-lg tracking-tight text-foreground">
              NeuralFeed
            </h1>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setSearchOpen(true)}
                className="p-2 rounded-lg hover:bg-muted transition-colors"
                aria-label="Search"
              >
                <Search className="h-4 w-4 text-muted-foreground" />
              </button>
              <RefreshIndicator />
            </div>
          </div>

          {/* View tabs + count + filter — present on every breakpoint */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              {([["foryou", "For You"], ["all", "All items"]] as const).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setView(key)}
                  className={cn(
                    "px-3.5 py-1.5 rounded-full text-sm font-medium border transition-colors",
                    view === key
                      ? "bg-foreground text-background border-foreground"
                      : "border-border text-muted-foreground hover:bg-muted"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-3">
              {!isLoading && !isError && total > 0 && (
                <span className="hidden text-xs text-muted-foreground tabular-nums sm:inline">
                  {/* V7-6: finite ranked shortlist — never a firehose */}
                  top {total}
                </span>
              )}
              <button
                onClick={() => setDrawerOpen(true)}
                className="relative flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted"
                aria-label="Filters"
              >
                <SlidersHorizontal className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Filters</span>
                {activeFilterCount > 0 && (
                  <span className="ml-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[9px] font-bold text-primary-foreground">
                    {activeFilterCount}
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* Horizon selector — the Feed is the most important + relevant items over
              the chosen window (Day = today's top N), as one finite numbered list. */}
          <div className="flex items-center justify-between gap-2 pt-1">
            <h2 className="font-serif text-lg font-semibold tracking-tight text-foreground">
              {horizon === "day" ? "Today in AI" : horizon === "year" ? "This year in AI" : "This month in AI"}
            </h2>
            <div className="flex items-center gap-1 rounded-full border border-border p-0.5">
              {HORIZON_LABEL.map(([h, label]) => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  aria-pressed={horizon === h}
                  className={cn(
                    "rounded-full px-3 py-1 text-xs font-medium transition-colors",
                    horizon === h
                      ? "bg-foreground text-background"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {isLoading && (
            <>
              <p className="text-xs text-muted-foreground text-center">
                Loading — the free server naps when idle, first load can take a minute…
              </p>
              {Array.from({ length: 6 }).map((_, i) => <FeedCardSkeleton key={i} />)}
            </>
          )}

          {isError && (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <AlertCircle className="h-8 w-8 text-destructive" />
              <p className="text-sm text-muted-foreground">Failed to load feed.</p>
              <button onClick={() => refetch()} className="text-sm text-primary hover:underline">
                Try again
              </button>
            </div>
          )}

          {!isLoading && !isError && allItems.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <Inbox className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No items match your filters.</p>
              <p className="text-xs text-muted-foreground">Try refreshing or broadening your filters.</p>
            </div>
          )}

          {!isLoading && !isError && allItems.length > 0 && (
            <div className="space-y-3">
              {allItems.map((article, i) => (
                <FeedCard key={article.id} article={article} onOpen={setOpenArticle} rank={i + 1} boxed />
              ))}
            </div>
          )}

          {/* V7-6: the Feed is a finite, numbered shortlist — no "Show more" here.
              Exploration (paginated) lives in Discover. */}
          {!isLoading && !isError && allItems.length > 0 && (
            <div className="py-6 text-center">
              <p className="font-serif text-sm font-semibold text-foreground">
                Your ranked top {total} — that&apos;s the signal worth your time today.
              </p>
              <button
                onClick={() => router.push("/discover")}
                className="mt-2 text-sm text-primary hover:underline"
              >
                Explore more in Discover →
              </button>
            </div>
          )}
        </main>
      </div>

      <FilterDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
      <SummarySheet article={openArticle} onClose={() => setOpenArticle(null)} />
    </div>
  );
}
