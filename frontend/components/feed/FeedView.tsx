"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search, AlertCircle, Inbox } from "lucide-react";
import { FeedCard } from "./FeedCard";
import { FeedCardSkeleton } from "./FeedCardSkeleton";
import { FilterBar } from "./FilterBar";
import { FilterDrawer } from "./FilterDrawer";
import { RefreshIndicator } from "./RefreshIndicator";
import { SearchModal } from "./SearchModal";
import { StoryCard } from "./StoryCard";
import { SummarySheet } from "./SummarySheet";
import { useInfiniteFeed, useStories } from "@/hooks/useFeed";
import { cn } from "@/lib/utils";
import type { Article, FeedFilters } from "@/lib/types";

const TIME_TO_DAYS: Record<string, number> = { "1d": 1, "3d": 3, "7d": 7, "30d": 30 };

export function FeedView() {
  const params = useSearchParams();
  const router = useRouter();
  const [searchOpen, setSearchOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [openArticle, setOpenArticle] = useState<Article | null>(null);

  const filters: FeedFilters = {
    category:    (params.get("category") as FeedFilters["category"]) || undefined,
    topic:       (params.get("topic") as FeedFilters["topic"]) || undefined,
    source_id:   params.get("source_id") || undefined,
    time_range:  (params.get("time_range") as FeedFilters["time_range"]) || "7d",
    is_read:     params.get("is_read") === "false" ? false : params.get("is_read") === "true" ? true : undefined,
    is_bookmarked: params.get("is_bookmarked") === "true" ? true : undefined,
    ranked:      params.get("ranked") === "true" ? true : undefined,
    feedback:    params.get("feedback") ? Number(params.get("feedback")) as FeedFilters["feedback"] : undefined,
    min_signal:  params.get("min_signal") ? Number(params.get("min_signal")) : undefined,
    limit: 30,
  };

  // Digest (story-first, finite) is the default; list view when the user asks
  // for "all", uses category/source filters, or browses saved items.
  const wantsList =
    params.get("view") === "all" ||
    !!filters.category ||
    !!filters.source_id ||
    !!filters.is_bookmarked ||
    filters.feedback !== undefined;
  const digestMode = !wantsList;

  const {
    data: infData, isLoading, isError, refetch,
    fetchNextPage, hasNextPage, isFetchingNextPage,
  } = useInfiniteFeed(filters);
  const allItems = infData?.pages.flatMap((p) => p.items) ?? [];
  const total = infData?.pages[0]?.total ?? 0;

  // Infinite scroll sentinel
  const sentinelRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el || digestMode) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) fetchNextPage();
      },
      { rootMargin: "600px" }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [digestMode, hasNextPage, isFetchingNextPage, fetchNextPage]);
  const storiesQuery = useStories({
    days: TIME_TO_DAYS[filters.time_range ?? "7d"] ?? 1,
    limit: 12,
    unread_only: filters.is_read === undefined ? true : filters.is_read === false,
    topic: filters.topic,
  });

  function setView(view: "digest" | "all") {
    const next = new URLSearchParams(params.toString());
    if (view === "all") next.set("view", "all");
    else {
      next.delete("view");
      // digest doesn't support these — clear so the toggle actually switches
      next.delete("category");
      next.delete("source_id");
      next.delete("is_bookmarked");
      next.delete("feedback");
    }
    router.push(`?${next.toString()}`, { scroll: false });
  }

  return (
    <div className="flex min-h-screen">
      {/* Single centered column on every breakpoint — no sidebar clutter */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* Filter bar */}
        <FilterBar onFilterClick={() => setDrawerOpen(true)} />

        <main className="flex-1 px-4 pt-4 pb-24 md:pb-6 lg:pb-8 max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto w-full space-y-3">
          {/* Mobile top bar */}
          <div className="flex items-center justify-between lg:hidden">
            <h1 className="font-serif font-bold text-base tracking-tight text-gradient-brand">NeuralFeed</h1>
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

          {/* Desktop top bar */}
          <div className="hidden lg:flex items-center justify-between pb-2">
            <h1 className="font-bold text-lg tracking-tight">Feed</h1>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSearchOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground border border-border rounded-lg hover:bg-muted transition-colors"
                aria-label="Search"
              >
                <Search className="h-3.5 w-3.5" />
                Search…
                <kbd className="ml-2 text-[10px] text-muted-foreground/60 border border-border rounded px-1">⌘K</kbd>
              </button>
              <RefreshIndicator />
            </div>
          </div>

          {/* Digest / All toggle */}
          <div className="flex items-center gap-1 rounded-full bg-muted p-0.5 w-fit" role="tablist" aria-label="Feed view">
            {([["digest", "Digest"], ["all", "All items"]] as const).map(([value, label]) => (
              <button
                key={value}
                role="tab"
                aria-selected={digestMode === (value === "digest")}
                onClick={() => setView(value)}
                className={cn(
                  "px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all min-h-[32px]",
                  digestMode === (value === "digest")
                    ? "bg-gradient-brand text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {label}
              </button>
            ))}
          </div>

          {digestMode ? (
            <>
              {/* Story digest — bounded, finite by design */}
              {storiesQuery.isLoading && (
                <>
                  <p className="text-xs text-muted-foreground text-center">
                    Loading your briefing — the free server naps when idle, first load can take a minute…
                  </p>
                  {Array.from({ length: 5 }).map((_, i) => <FeedCardSkeleton key={i} />)}
                </>
              )}

              {storiesQuery.isError && (
                <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
                  <AlertCircle className="h-8 w-8 text-destructive" />
                  <p className="text-sm text-muted-foreground">Failed to load stories.</p>
                  <button onClick={() => storiesQuery.refetch()} className="text-sm text-primary hover:underline">
                    Try again
                  </button>
                </div>
              )}

              {storiesQuery.data?.stories.map((story) => (
                <StoryCard key={story.id} story={story} onOpenArticle={setOpenArticle} />
              ))}

              {storiesQuery.data && storiesQuery.data.stories.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
                  <Inbox className="h-8 w-8 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Nothing new right now.</p>
                  <p className="text-xs text-muted-foreground">Check back later or pull a manual refresh.</p>
                </div>
              )}

              {/* The end-cap: the feed is finite */}
              {storiesQuery.data && storiesQuery.data.stories.length > 0 && (
                <div className="py-8 text-center space-y-2">
                  {storiesQuery.data.caught_up ? (
                    <p className="font-serif text-base font-semibold text-gradient-brand">
                      ✦ You&apos;re all caught up
                    </p>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Showing top {storiesQuery.data.stories.length} of {storiesQuery.data.total_stories} stories
                    </p>
                  )}
                  <button
                    onClick={() => setView("all")}
                    className="text-xs text-primary hover:underline"
                  >
                    Browse all items
                  </button>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Classic list view */}
              {isLoading && Array.from({ length: 6 }).map((_, i) => <FeedCardSkeleton key={i} />)}

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

              {/* Infinite scroll sentinel + status */}
              <div ref={sentinelRef} aria-hidden />
              {isFetchingNextPage && Array.from({ length: 3 }).map((_, i) => <FeedCardSkeleton key={`p${i}`} />)}
              {!hasNextPage && allItems.length > 0 && (
                <p className="py-6 text-center text-xs text-muted-foreground">
                  All {total} items loaded
                </p>
              )}
            </>
          )}
        </main>
      </div>

      {/* Mobile/tablet filter drawer */}
      <FilterDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />

      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />

      <SummarySheet article={openArticle} onClose={() => setOpenArticle(null)} />
    </div>
  );
}
