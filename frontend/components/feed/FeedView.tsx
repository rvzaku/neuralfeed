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
import { useInfiniteFeed } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";
import type { Article, FeedFilters } from "@/lib/types";

const FILTER_PARAMS = ["category", "topic", "source_id", "time_range", "is_read", "is_bookmarked", "feedback", "min_signal"];

export function FeedView() {
  const params = useSearchParams();
  const router = useRouter();
  const [searchOpen, setSearchOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [openArticle, setOpenArticle] = useState<Article | null>(null);

  // "For You" = ranked + personalized; "All" = raw chronological
  const view = params.get("view") === "all" ? "all" : "foryou";

  const filters: FeedFilters = useMemo(() => ({
    category:    (params.get("category") as FeedFilters["category"]) || undefined,
    topic:       (params.get("topic") as FeedFilters["topic"]) || undefined,
    source_id:   params.get("source_id") || undefined,
    time_range:  (params.get("time_range") as FeedFilters["time_range"]) || "7d",
    is_read:     params.get("is_read") === "false" ? false : params.get("is_read") === "true" ? true : undefined,
    is_bookmarked: params.get("is_bookmarked") === "true" ? true : undefined,
    feedback:    params.get("feedback") ? Number(params.get("feedback")) as FeedFilters["feedback"] : undefined,
    min_signal:  params.get("min_signal") ? Number(params.get("min_signal")) : undefined,
    ranked:      true,            // V6: smart ranking is never disabled
    include_read: view === "all", // "All items" = ranked archive incl. viewed
    limit: 30,
  }), [params, view]);

  const activeFilterCount = FILTER_PARAMS.filter((k) => params.get(k)).length;

  const {
    data: infData, isLoading, isError, refetch,
    fetchNextPage, hasNextPage, isFetchingNextPage,
  } = useInfiniteFeed(filters);
  const allItems = infData?.pages.flatMap((p) => p.items) ?? [];
  const total = infData?.pages[0]?.total ?? 0;

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

          {/* Top bar: brand, tabs, actions — filters stay behind one button */}
          <div className="flex items-center justify-between gap-2">
            <h1 className="font-serif font-bold text-base tracking-tight text-foreground lg:text-lg">
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
              <button
                onClick={() => setDrawerOpen(true)}
                className="relative p-2 rounded-lg hover:bg-muted transition-colors"
                aria-label="Filters"
              >
                <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
                {activeFilterCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-primary text-primary-foreground text-[9px] font-bold flex items-center justify-center">
                    {activeFilterCount}
                  </span>
                )}
              </button>
              <RefreshIndicator />
            </div>
          </div>

          {/* View tabs + a precise, calm count — never a firehose (V6) */}
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
            {!isLoading && !isError && total > 0 && (
              <span className="text-xs text-muted-foreground tabular-nums">
                {/* V6: finite framing — never a firehose */}
                {allItems.length < total
                  ? `Showing ${allItems.length} of ${total}`
                  : `${total} ${total === 1 ? "article" : "articles"}`}
              </span>
            )}
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

          {!isLoading && !isError && allItems.map((article) => (
            <FeedCard key={article.id} article={article} onOpen={setOpenArticle} />
          ))}

          {/* No infinite scroll (app-feedback-v5): the feed is finite and
              deliberate — an explicit button pages deeper when wanted */}
          {isFetchingNextPage && Array.from({ length: 3 }).map((_, i) => <FeedCardSkeleton key={`p${i}`} />)}
          {hasNextPage && !isFetchingNextPage && allItems.length > 0 && (
            <button
              onClick={() => fetchNextPage()}
              className="w-full py-3 text-sm font-medium text-muted-foreground border border-border rounded-xl hover:bg-muted transition-colors"
            >
              Show more
            </button>
          )}
          {!hasNextPage && allItems.length > 0 && (
            <p className="py-6 text-center text-sm font-serif font-semibold text-foreground">
              {view === "foryou"
                ? `You're all caught up — ${total} items earned a slot in this window`
                : `All ${total} items loaded`}
            </p>
          )}
        </main>
      </div>

      <FilterDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
      <SummarySheet article={openArticle} onClose={() => setOpenArticle(null)} />
    </div>
  );
}
